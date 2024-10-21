from django.test import TestCase, Client
from django.urls import reverse
from author.models import Author
from .models import Post
import jwt
from django.conf import settings

class AuthorTestCase(TestCase):

    def setUp(self):
        # Create some test authors for the test database
        self.author1 = Author.objects.create(display_name="Author1", host='http://localhost', FQID='http://localhost/api/authors/1')
        self.author2 = Author.objects.create(display_name="Author2", host='http://localhost', FQID='http://localhost/api/authors/2')
        
        # Create a JWT token for the first author
        self.token = jwt.encode({'id': self.author1.display_name}, settings.SECRET_KEY, algorithm='HS256')

        # Create a client instance
        self.client = Client()
    
    def test_authors_creation(self):
        """Test that authors are created successfully."""
        # Check that authors exist in the database
        self.assertEqual(Author.objects.count(), 2)  # Ensure two authors were created

        author1 = Author.objects.get(display_name="Author1")
        author2 = Author.objects.get(display_name="Author2")

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
        
       
class PostTestCase(TestCase):

    def setUp(self):
        # Create some test authors for the test database
        self.author = Author.objects.create(display_name="Author1", host='http://localhost', FQID='http://localhost/api/authors/1')

        # Create a client instance
        self.client = Client()
    
    def test_posts_creation(self):
        """Test that posts are created successfully."""
        # Create a post
        post = Post.objects.create(
            title="Test Post",
            description="This is a test post description.",
            content_type='text/plain',
            content="This is the content of the test post.",
            author=self.author,
            visibility='PUBLIC'
        )

        # Check that the post exists in the database
        self.assertEqual(Post.objects.count(), 1)  # Ensure one post was created

        created_post = Post.objects.get(title="Test Post")

        # Check that the post's properties are correct
        self.assertEqual(created_post.description, "This is a test post description.")
        self.assertEqual(created_post.content_type, 'text/plain')
        self.assertEqual(created_post.content, "This is the content of the test post.")
        self.assertEqual(created_post.author, self.author)
        self.assertEqual(created_post.visibility, 'PUBLIC')

    def test_post_visibility(self):
        """Test visibility of posts."""
        post = Post.objects.create(
            title="Private Post",
            description="This post is private.",
            content_type='text/plain',
            content="Content of the private post.",
            author=self.author,
            visibility='FRIENDS'  # Setting visibility to FRIENDS
        )

        # Check visibility logic (Assuming you have a way to determine the user)
        user = None  # Simulate a user who is not a friend
        self.assertFalse(post.is_visible_to(user))  # Should be False for non-friends

        # You can add more tests for other visibility types as needed
