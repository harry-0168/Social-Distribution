from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from author.models import Author
import json
from unittest.mock import Mock, patch
import uuid  


class NodeAdminAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create test authors for use in API testing
        self.author1 = Author.objects.create(
            displayName="Author One",
            github="https://github.com/author1",
            host="http://localhost"
        )
        self.author2 = Author.objects.create(
            displayName="Author Two",
            github="https://github.com/author2",
            host="http://localhost"
        )

    ### Test API Endpoints ###

    # Test for API to list authors (GET /api/authors/)
    def test_list_authors(self):
        response = self.client.get(reverse('api_list_authors'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("authors", response.json())
        self.assertEqual(len(response.json()["authors"]), 2)  # Ensure two authors are returned

    # Test for adding a new author (POST /api/authors/add/)
    def test_add_author(self):
        author_data = {
            'displayName': 'New Author',
            'github': 'https://github.com/newauthor',
            'profile_image': '',  # No image for now
            'page': ''
        }
        response = self.client.post(reverse('api_add_author'), data=author_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["message"], "Author created successfully")
        self.assertTrue(Author.objects.filter(displayName='New Author').exists())

    # Test for API to retrieve a single author detail (GET /api/authors/<int:author_id>/)
    def test_get_author_detail(self):
        author_id = self.author1.id
        
        # Mock the profile_image field to avoid serialization issues
        with patch('author.models.Author.profile_image', new_callable=Mock):
            response = self.client.get(reverse('api_author_detail', args=[author_id]))
        
        # Expecting a 200 OK status
        self.assertEqual(response.status_code, 200)
        
        # Parse the response JSON
        data = response.json()
        
        # Check the expected fields, ignoring 'profile_image'
        self.assertEqual(data["displayName"], "Author One")
        self.assertEqual(data["github"], "https://github.com/author1")

    # Test for API to update an author (PUT /api/authors/<int:author_id>/)
    def test_update_author(self):
        author_id = self.author1.id
        update_data = json.dumps({
            'displayName': 'Updated Author One',
            'github': 'https://github.com/updatedauthor',
            'profile_image': 'new_image_url',
            'page': '/new_page'
        })
        response = self.client.put(
            reverse('api_author_detail', args=[author_id]),
            data=update_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Author modified successfully")

        # Ensure the author was updated in the database
        self.author1.refresh_from_db()
        self.assertEqual(self.author1.displayName, 'Updated Author One')
        self.assertEqual(self.author1.github, 'https://github.com/updatedauthor')

    # Test for API to delete an author (DELETE /api/authors/<int:author_id>/delete/)
    def test_delete_author(self):
        author_id = self.author1.id
        response = self.client.delete(reverse('api_delete_author', args=[author_id]))
        self.assertEqual(response.status_code, 204)

        # Ensure the author was deleted from the database
        self.assertFalse(Author.objects.filter(id=author_id).exists())

    ### Test Error Handling ###

    # Test for retrieving a non-existent author (GET /api/authors/<int:author_id>/)

    def test_get_author_detail_not_found(self):
        # Generate a random, non-existent UUID
        non_existent_author_id = uuid.uuid4()
        
        # Perform the GET request using the generated UUID
        response = self.client.get(reverse('api_author_detail', args=[non_existent_author_id]))
        
        # Expecting a 404 Not Found status
        self.assertEqual(response.status_code, 404)


    # Test for updating a non-existent author (PUT /api/authors/<int:author_id>/)
    def test_add_author_with_empty_displayName_and_github(self):
        # Prepare data with empty displayName and arbitrary github value (no validation on github)
        invalid_author_data = {
            'displayName': '',  # Empty displayName is allowed
            'github': 'invalid_github_url'  # No validation on github field
        }
        
        # Perform the POST request to create the author
        response = self.client.post(reverse('api_add_author'), data=invalid_author_data)
        
        # Expect a 201 Created status code since the data is valid according to the model
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], "Author created successfully")

        # Ensure the new author is created in the database with the provided values
        new_author = Author.objects.get(github='invalid_github_url')  # Find by github field
        self.assertEqual(new_author.displayName, '')  # Display name should be empty
        self.assertEqual(new_author.github, 'invalid_github_url')  # GitHub field should match the input


    # Test for invalid PUT request data when updating an author (PUT /api/authors/<int:author_id>/)
    def test_update_author_with_empty_displayName_and_github(self):
        author_id = self.author1.id
        update_data = json.dumps({
            'displayName': '',  # Empty displayName is allowed, so no error expected
            'github': 'invalid_github_url'  # No validation on github, so this is just treated as a string
        })
        
        # Perform the PUT request to update the author
        response = self.client.put(
            reverse('api_author_detail', args=[author_id]),
            data=update_data,
            content_type='application/json'
        )
        
        # Expecting 200 OK because there's no validation on these fields
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()["message"], "Author modified successfully")

        # Fetch the updated author and confirm the changes
        updated_author = Author.objects.get(id=author_id)
        self.assertEqual(updated_author.displayName, '')  # Ensure the displayName is updated to empty
        self.assertEqual(updated_author.github, 'invalid_github_url')  # Ensure the github field is updated
