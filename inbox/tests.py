from django.test import TestCase

# Create your tests here.
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from .models import Author,  Inbox
from author.models import Following
import jwt
from django.conf import settings
from datetime import datetime, timedelta


class InboxApiTestCase(APITestCase):
    
    def setUp(self):
        # Create two authors for the follow request tests
        self.author1 = Author.objects.create(
            displayName="Greg Johnson", 
            FQID="http://nodeaaaa/api/authors/111", 
            host="http://nodeaaaa/api/"
        )
        self.author2 = Author.objects.create(
            displayName="Lara Croft", 
            FQID="http://nodebbbb/api/authors/222", 
            host="http://nodebbbb/api/"
        )
        
        # Generate JWT token for author1
        payload = {
        'id': self.author1.displayName,
        'author_id': str(self.author1.id),
        'exp': datetime.now() + timedelta(days=1),  # Token expiration
        'iat': datetime.now()
        }
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Setup the client and attach token as a cookie
        self.client = APIClient()
        self.client.cookies['jwt'] = self.token

        # URL for the inbox API
        self.url = reverse('inboxApi', kwargs={'object_author_id': self.author2.id})
    
    def test_follow_request_success(self):
        """
        Test if a valid follow request is processed successfully.
        """
        data = {
            "type": "follow",
            "summary": "Greg wants to follow Lara",
            "actor": {
                "type": "author",
                "id": self.author1.FQID,
                "host": self.author1.host,
                "displayName": self.author1.displayName,
                "github": "http://github.com/gjohnson",
                "profileImage": "https://i.imgur.com/k7XVwpB.jpeg",
                "page": "http://nodeaaaa/authors/greg"
            },
            "object": {
                "type": "author",
                "id": self.author2.FQID,
                "host": self.author2.host,
                "displayName": self.author2.displayName,
                "page": "http://nodebbbb/authors/222",
                "github": "http://github.com/laracroft",
                "profileImage": "http://nodebbbb/api/authors/222/posts/217/image"
            }
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Follow request sent')

    def test_follow_yourself(self):
        """
        Test if trying to follow yourself returns the appropriate error.
        """
        data = {
            "type": "follow",
            "summary": "Greg wants to follow Greg",
            "actor": {
                "type": "author",
                "id": self.author1.FQID,
                "host": self.author1.host,
                "displayName": self.author1.displayName
            },
            "object": {
                "type": "author",
                "id": self.author1.FQID,  # Actor and object are the same
                "host": self.author1.host,
                "displayName": self.author1.displayName
            }
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Cannot follow yourself')

    def test_already_following(self):
        """
        Test if trying to follow someone you're already following returns an error.
        """
        # Create a following relationship
        Following.follow(self.author1, self.author2)

        data = {
            "type": "follow",
            "summary": "Greg wants to follow Lara again",
            "actor": {
                "type": "author",
                "id": self.author1.FQID,
                "host": self.author1.host,
                "displayName": self.author1.displayName
            },
            "object": {
                "type": "author",
                "id": self.author2.FQID,
                "host": self.author2.host,
                "displayName": self.author2.displayName
            }
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Already following')

    def test_unauthenticated(self):
        """
        Test if no JWT token leads to an unauthenticated error.
        """
        self.client.cookies.clear()  # Remove the JWT cookie
        
        data = {
            "type": "follow",
            "summary": "Greg wants to follow Lara",
            "actor": {
                "type": "author",
                "id": self.author1.FQID,
                "host": self.author1.host,
                "displayName": self.author1.displayName
            },
            "object": {
                "type": "author",
                "id": self.author2.FQID,
                "host": self.author2.host,
                "displayName": self.author2.displayName
            }
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Unauthenticated')

    def test_invalid_token(self):
        """
        Test if an invalid JWT token leads to an invalid token error.
        """
        # Set an invalid token
        self.client.cookies['jwt'] = 'invalid_token'

        data = {
            "type": "follow",
            "summary": "Greg wants to follow Lara",
            "actor": {
                "type": "author",
                "id": self.author1.FQID,
                "host": self.author1.host,
                "displayName": self.author1.displayName
            },
            "object": {
                "type": "author",
                "id": self.author2.FQID,
                "host": self.author2.host,
                "displayName": self.author2.displayName
            }
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid token')


