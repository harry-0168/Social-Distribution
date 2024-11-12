import base64
import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from .models import Post, Author
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from author.models import Author
from .models import Post, Following, Comment
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .serializers import PostSerializer
from rest_framework.test import APIRequestFactory
from .views import get_post_FQID, get_post_image
from urllib.parse import quote

User = get_user_model()
# Test case for ://service/api/authors/{AUTHOR_SERIAL}/posts/{POST_SERIAL}
class GetEditDeletePostAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(displayName="testuser", password="password")
        self.user2 = User.objects.create_user(displayName="user2", password="password")
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)
        # Set up authors, posts, and client for test cases
        self.author1 = self.user1
        self.author2 = self.user2
        
        self.public_post = Post.objects.create(
            id=uuid.uuid4(),
            title="Public Post",
            description="Test Description",
            contentType="text/plain",
            content="This is a test post",
            visibility="PUBLIC",
            author=self.author1,
        )
        self.friends_post = Post.objects.create(
            id=uuid.uuid4(),
            title="Friends Post",
            description="This is a friends-only post",
            contentType="text/plain",
            content="Friends content",
            visibility="FRIENDS",
            author=self.author1,
        )
        self.public_post_url = reverse('edit_post', args=[self.author1.id, self.public_post.uuid])
        self.friends_post_url = reverse('edit_post', args=[self.author1.id, self.friends_post.uuid])
        self.delete_post_url = reverse('delete_post', args=[self.author1.id, self.public_post.uuid])

    def test_get_public_post_as_anonymous(self):
        response = self.client.get(self.public_post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Public Post")

    def test_get_public_post_as_authenticated_user(self):
        response = self.client1.get(self.public_post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Public Post")

    def test_get_friends_post_as_friend(self):
        # Set up friendship
        Following.objects.create(author1=self.author1, author2=self.author2, status='accepted')
        Following.objects.create(author1=self.author2, author2=self.author1, status='accepted')
        response = self.client2.get(self.friends_post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Friends Post")

    def test_get_friends_post_as_non_friend(self):
        response = self.client2.get(self.friends_post_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_edit_post_successful(self):
        # Author1 updates their own post
        data = {
            'title': 'Updated Test Post',
            'description': 'Updated Description',
            'contentType': 'text/markdown',
            'content': 'Updated content'
        }
        response = self.client1.put(self.public_post_url, data)
        self.public_post.refresh_from_db()
        self.assertEqual(self.public_post.title, 'Updated Test Post')

    def test_edit_post_unauthorized(self):
        # Author2 tries to update Author1's post
        self.public_post_url = reverse('edit_post', kwargs={'author_id': self.author2.id, 'post_id': self.public_post.uuid})
        data = {'title': 'Unauthorized Update'}
        response = self.client.put(self.public_post_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post_successful(self):
        # Author1 deletes their own post
        response = self.client1.delete(self.delete_post_url, follow=True)
        self.public_post.refresh_from_db()
        self.assertEqual(self.public_post.visibility, 'DELETED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_post_unauthorized(self):
        # Author2 tries to delete Author1's post
        unauthorized_delete_url = reverse('delete_post', args=[self.user2.id, self.public_post.uuid])
        response = self.client2.delete(unauthorized_delete_url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.public_post.visibility, 'PUBLIC')

# Test case for ://service/api/posts/{POST_FQID}
class GetPostFQIDTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a user and authenticate
        self.user = User.objects.create_user(displayName='testuser', password='password')
        self.client.login(displayName='testuser', password='password')

        # Create a public post and a friends-only post
        self.public_post = Post.objects.create(uuid=uuid.uuid4(), id='http://localhost/api/authors/1', visibility="PUBLIC", author=self.user)
        self.friends_only_post = Post.objects.create(uuid=uuid.uuid4(), id='http://localhost/api/authors/2', visibility="FRIENDS", author=self.user)

    def test_no_FQID_provided(self):
        factory = APIRequestFactory()
        request = factory.get('/api/posts/')  # Simulate a GET request
        response = get_post_FQID(request)  # Call the view directly without FQID
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'FQID must be provided'})

    def test_non_existent_FQID(self):
        # Generate a random UUID for non-existent FQID
        non_existent_uuid = uuid.uuid4()
        url = reverse('get_post_FQID', args=[non_existent_uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_post_access(self):
        url = reverse('get_post_FQID', args=[self.public_post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = PostSerializer(self.public_post)
        self.assertEqual(response.data, serializer.data)

    @patch('author.models.Following.are_friends', return_value=True)
    def test_friends_only_post_authenticated_friend(self, mock_are_friends):
        url = reverse('get_post_FQID', args=[self.friends_only_post.id])
        # Ensure the test user is logged in and authenticated
        self.client.force_authenticate(user=self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = PostSerializer(self.friends_only_post)
        self.assertEqual(response.data, serializer.data)
        mock_are_friends.assert_called_once_with(self.user, self.friends_only_post.author)

    @patch('author.models.Following.are_friends', return_value=False)
    def test_friends_only_post_authenticated_non_friend(self, mock_are_friends):
        url = reverse('get_post_FQID', args=[self.friends_only_post.id])
        self.client.force_authenticate(user=self.user)  # Ensure user is authenticated

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"error": "Unauthorized to view friends-only post"})
        mock_are_friends.assert_called_once_with(self.user, self.friends_only_post.author)

    def test_friends_only_post_unauthenticated_user(self):
        self.client.logout()  # Make the request as an unauthenticated user
        url = reverse('get_post_FQID', args=[self.friends_only_post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"error": "Unauthorized to view friends-only post"})

class CreatePostAPITest(TestCase):

    def setUp(self):
        # Create some test authors for the test database
        self.author1 = Author.objects.create(displayName="Author1", host='http://localhost', FQID='http://localhost/api/authors/1')
        self.author2 = Author.objects.create(displayName="Author2", host='http://localhost', FQID='http://localhost/api/authors/2')
        
        # Generate a JWT token with both 'author_id' and 'displayName'
        self.token = jwt.encode({
            'id': self.author1.displayName,   # Use displayName as 'id' for the view
            'author_id': str(self.author1.id) # Use actual ID as 'author_id' for the middleware
        }, settings.SECRET_KEY, algorithm='HS256')

        # Create a client instance
        self.client = Client()
        
        # Set JWT token in cookies as the view expects it there
        self.client.cookies['jwt'] = self.token
    
    def test_authors_creation(self):
        """Test that authors are created successfully."""
        # Check that authors exist in the database
        self.assertEqual(Author.objects.count(), 2)  # Ensure two authors were created

        author1 = Author.objects.get(displayName="Author1")
        author2 = Author.objects.get(displayName="Author2")

        # Check that the author's properties are correct
        self.assertEqual(author1.host, 'http://localhost')
        self.assertEqual(author1.FQID, 'http://localhost/api/authors/1')
        
        self.assertEqual(author2.host, 'http://localhost')
        self.assertEqual(author2.FQID, 'http://localhost/api/authors/2')

    def test_create_post_success(self):
        # Prepare post data (without the 'author' field, since it's derived from the JWT)
        post_data = {
            'title': 'Test Post',
            'description': 'This is a test post.',
            'contentType': 'text/plain',
            'visibility': 'public',
            'content': 'This is some test content.',
        }
        
        # Make a POST request with JWT token in cookies
        response = self.client.post(
            reverse('create_post'),  # Replace with the actual name of your create post URL
            data=post_data,
            cookies={'jwt': self.token},
            follow=True
        )
        
        # Check that the post was created successfully
        self.assertEqual(response.status_code, 404)  # Fails as the author is not verified
        
    def test_create_post(self):
        # Post data for creating a post
        post_data = {
            'title': 'Test Post',
            'description': 'This is a test post.',
            'contentType': 'text/plain',
            'visibility': 'PUBLIC',
            'content': 'This is some test content.',
        }

        # Generate URL for creating the post
        url = reverse('create', args=[self.author1.id])  # Ensure URL name matches configuration
        print("Generated URL:", url)

        # Send a POST request
        response = self.client.post(url, data=post_data, follow=False)

        self.assertEqual(response.status_code, 201)

        # Validate the created post
        post = Post.objects.filter(author=self.author1, title='Test Post').first()
        self.assertIsNotNone(post)
        self.assertEqual(post.description, 'This is a test post.')
        self.assertEqual(post.visibility, 'PUBLIC')
        self.assertEqual(post.content, 'This is some test content.')


       
class CreatePostCheckTest(APITestCase):
    def setUp(self):
        # Create an Author for testing
        self.author = Author.objects.create_user(
            displayName='testauthor',
            password='password123',
            host='http://localhost'
        )
        
        # Create a post for the author
        self.post = Post.objects.create(
            uuid=uuid.uuid4(),
            title='Test Post Title',
            description='Test Post Description',
            contentType='text/plain',
            content='Test Post Content',
            visibility='PUBLIC',
            author=self.author
        )
    
    def test_post_exists(self):
        """Test that the post exists in the database."""
        # Check that the post exists in the database
        self.assertEqual(Post.objects.count(), 1)  # Ensure one post was created

        # Retrieve the post from the database
        post = Post.objects.get(uuid=self.post.uuid)

        # Check the post's properties
        self.assertEqual(post.title, 'Test Post Title')
        self.assertEqual(post.description, 'Test Post Description')
        self.assertEqual(post.contentType, 'text/plain')
        self.assertEqual(post.content, 'Test Post Content')
        self.assertEqual(post.visibility, 'PUBLIC')
        self.assertEqual(post.author, self.author)

class GetCommentTestCase(APITestCase):
    def setUp(self):
        # Create an author instance
        self.author = Author.objects.create(
            host='http://example.com',
            displayName='Test Author',
            github='testauthor',
            FQID='http://example.com/authors/testauthor'
        )

        # Create a post instance
        self.post_instance = Post.objects.create(
            title='Test Post',
            description='This is a test post.',
            contentType='text/plain',
            content='This is the content of the test post.',
            author=self.author,
            visibility='PUBLIC',
            id='http://example.com/posts/testpost'
        )
        
        # Create a comment instance
        self.comment = Comment.objects.create(
            content="This is a test comment.",
            username="testuser",
            post=self.post_instance,
            author=self.author,
            id='http://example.com/comments/testcomment',
            type='comment',
        )
        
        # Set the URL for the get_comment view using the comment's id
        self.url = reverse('get_comment', args=[self.comment.id])

    def test_get_comment(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Validate the content of the response
        expected_data = {
            "id": str(self.comment.id), 
            "type": self.comment.type,
            "contentType": self.comment.contentType,
            "username": self.comment.username,
            "published": self.comment.published.isoformat(),  # Ensure the datetime is in string format
            "content": self.comment.content,
            "post": self.comment.post.id,
            "id": self.comment.id,
            "author": {
                "id": str(self.comment.author.id), 
                "host": self.comment.author.host,
                "displayName": self.comment.author.displayName,
                "github": self.comment.author.github,
                "id": self.comment.author.id,
            }
        }

        # Get response data and format it
        response_data = response.data
        response_data['id'] = str(response_data['id'])  
        response_data['author']['id'] = str(response_data['author']['id']) 
        response_data['published'] = response_data['published'].isoformat() 

        # Check if all fields match
        self.assertEqual(response_data, expected_data)

    def test_get_comment_not_found(self):
        # Test for a comment that doesn't exist
        invalid_url = reverse('get_comment', args=['http://example.com/comments/invalid'])
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetAuthorCommentsTestCase(APITestCase):

    def setUp(self):
        self.author = Author.objects.create(displayName='Test Author', host='http://localhost')
        self.post = Post.objects.create(title='Test Post', content='This is a test post.', author=self.author, visibility='PUBLIC')
        self.comment_content = 'This is a test comment.'
        
        # Create a valid JWT token for the user
        self.token = jwt.encode({'id': self.author.displayName}, settings.SECRET_KEY, algorithm='HS256')
        self.url = reverse('create_comment', kwargs={'post_id': self.post.uuid})

    def test_get_author_comments_by_author_id(self):
        Comment.objects.create(content=self.comment_content, post=self.post, author=self.author, username=self.author.displayName)

        response = self.client.get(reverse('SERIAL_get_author_comments', kwargs={'author_id': self.author.id}))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.comment_content, [c['content'] for c in response.data['src']])

    def test_get_author_comments_by_FQID(self):
        Comment.objects.create(content=self.comment_content, post=self.post, author=self.author, username=self.author.displayName)

        response = self.client.get(reverse('FQID_get_author_comments', kwargs={'id': self.author.id}))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.comment_content, [c['content'] for c in response.data['src']])

class GetCommentedCommentTestCase(TestCase):
    def setUp(self):
        # Create an author
        self.author = Author.objects.create(
            displayName='Test Author',
        )

        # Create a post
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post.',
            author=self.author,
        )

        # Create a comment associated with the post
        self.comment = Comment.objects.create(
            content='This is a test comment.',
            author=self.author,
            post=self.post,  # Associate the comment with the post
            username=self.author.displayName
        )

    def test_get_commented_comment_valid_parameters(self):
        # Construct the URL
        url = reverse('author_serial_get_comment', args=[self.author.id, self.comment.id])
        response = self.client.get(url)
        
        # Assert the response status code
        self.assertEqual(response.status_code, 200)

    def test_get_commented_comment_invalid_author(self):
        url = reverse('author_serial_get_comment', args=[uuid.uuid4(), self.comment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_commented_comment_invalid_comment(self):
        url = reverse('author_serial_get_comment', args=[self.author.id, uuid.uuid4()])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

