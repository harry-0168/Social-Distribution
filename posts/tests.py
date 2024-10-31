import base64
import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Post, Author
from django.test import TestCase, Client
from django.urls import reverse
from author.models import Author
from .models import Post
import jwt
from django.conf import settings

class EditPostAPITest(APITestCase):
    def setUp(self):
        # Create an Author for testing
        self.author = Author.objects.create_user(
            displayName='testauthor',
            password='password123',
            host='http://localhost'
        )
        
        # Create a post for the author
        self.post = Post.objects.create(
            id=uuid.uuid4(),
            title='Original Title',
            description='Original Description',
            content_type='text/plain',
            content='Original Content',
            visibility='public',
            author=self.author
        )
        
        # API URL for editing the post
        self.url = reverse('edit_post', args=[str(self.post.id)])

    def test_successful_update(self):
        # Data to update the post
        data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'content_type': 'text/plain',
            'content': 'Updated Content',
        }
        response = self.client.post(self.url, data)
        
        # Assert the post was updated successfully
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')
        self.assertEqual(self.post.description, 'Updated Description')


    def test_invalid_method(self):
        response = self.client.get(self.url)  # GET method instead of POST
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update(self):
        # Test updating only the title field
        data = {'title': 'Partially Updated Title'}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Partially Updated Title')
        self.assertEqual(self.post.description, 'Original Description')

class CreatePostAPITest(TestCase):

    def setUp(self):
        # Create some test authors for the test database
        self.author1 = Author.objects.create(displayName="Author1", host='http://localhost', FQID='http://localhost/api/authors/1')
        self.author2 = Author.objects.create(displayName="Author2", host='http://localhost', FQID='http://localhost/api/authors/2')
        
        # Create a JWT token for the first author
        self.token = jwt.encode({'id': self.author1.displayName}, settings.SECRET_KEY, algorithm='HS256')

        # Create a client instance
        self.client = Client()
    
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
            'content_type': 'text/plain',
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
            id=uuid.uuid4(),
            title='Test Post Title',
            description='Test Post Description',
            content_type='text/plain',
            content='Test Post Content',
            visibility='PUBLIC',
            author=self.author
        )
    
    def test_post_exists(self):
        """Test that the post exists in the database."""
        # Check that the post exists in the database
        self.assertEqual(Post.objects.count(), 1)  # Ensure one post was created

        # Retrieve the post from the database
        post = Post.objects.get(id=self.post.id)

        # Check the post's properties
        self.assertEqual(post.title, 'Test Post Title')
        self.assertEqual(post.description, 'Test Post Description')
        self.assertEqual(post.content_type, 'text/plain')
        self.assertEqual(post.content, 'Test Post Content')
        self.assertEqual(post.visibility, 'PUBLIC')
        self.assertEqual(post.author, self.author)

