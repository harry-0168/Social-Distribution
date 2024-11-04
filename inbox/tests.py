from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Author, Inbox, Post
from author.models import Author, Following
from posts.models import Like, Comment

import jwt
from django.conf import settings
from datetime import datetime, timedelta

class InboxTests(APITestCase):
    def setUp(self):
        # Create an author and set up login credentials
        self.author_password = "test_password"
        self.author = Author.objects.create(displayName="test_author", FQID="http://example.com/authors/1", isVerified=True)
        self.author.set_password(self.author_password)
        self.author.save()

        # Create a second author for interactions
        self.other_author = Author.objects.create(displayName="other_author", FQID="http://example.com/authors/2", isVerified=True)

        # Define URLs
        self.login_url = reverse('login')
        self.inbox_url = reverse('inbox')
        self.inbox_api_url = reverse('follow_request', kwargs={'object_author_id': self.author.id})
        self.follow_request_url = reverse('follow_request_response', kwargs={'author_id': self.author.id, 'foreign_author_fqid': self.other_author.FQID})
        self.get_followers_url = reverse('get_followers', kwargs={'author_id': self.author.id})
        self.get_following_url = reverse('get_following', kwargs={'author_id': self.author.id})

    def authenticate(self):
        # Perform login and store the JWT token in cookies
        response = self.client.post(self.login_url, data={'displayName': self.author.displayName, 'password': self.author_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Retrieve the JWT token from the login response cookie
        token = response.cookies.get(settings.JWT_AUTH_COOKIE).value
        self.client.cookies[settings.JWT_AUTH_COOKIE] = token

    def test_get_inbox_unauthenticated(self):
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_inbox_authenticated(self):
        self.authenticate()
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_send_follow_request(self):
        self.authenticate()
        follow_data = {
            "type": "follow",
            "actor": {
                "id": self.author.FQID,
                "host": "http://example.com/",
                "displayName": "test_author"
            },
            "object": {
                "id": self.other_author.FQID,
                "host": "http://example.com/",
                "displayName": "other_author"
            }
        }
        response = self.client.post(self.inbox_api_url, data=follow_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['requestStatus'], 'pending')
        self.assertEqual(Following.objects.filter(author1=self.author, author2=self.other_author).count(), 1)

    def test_accept_follow_request(self):
        self.authenticate()
        Following.objects.create(author1=self.other_author, author2=self.author, status='pending')
        response = self.client.put(self.follow_request_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        follow_request = Following.objects.get(author1=self.other_author, author2=self.author)
        self.assertEqual(follow_request.status, 'accepted')

    def test_reject_follow_request(self):
        self.authenticate()
        Following.objects.create(author1=self.other_author, author2=self.author, status='pending')
        response = self.client.delete(self.follow_request_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Following.objects.filter(author1=self.other_author, author2=self.author).exists())

    def test_get_followers(self):
        Following.objects.create(author1=self.other_author, author2=self.author, status='accepted')
        self.authenticate()
        response = self.client.get(self.get_followers_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'followers')
        self.assertEqual(len(response.data['followers']), 1)
        self.assertEqual(response.data['followers'][0]['displayName'], "other_author")

    def test_get_following(self):
        Following.objects.create(author1=self.author, author2=self.other_author, status='accepted')
        self.authenticate()
        response = self.client.get(self.get_following_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'following')
        self.assertEqual(len(response.data['following']), 1)
        self.assertEqual(response.data['following'][0]['displayName'], "other_author")
