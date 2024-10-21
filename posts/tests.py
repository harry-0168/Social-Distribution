import base64
import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Post, Author

class EditPostAPITest(APITestCase):
    def setUp(self):
        # Create an Author for testing
        self.author = Author.objects.create_user(
            display_name='testauthor',
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
