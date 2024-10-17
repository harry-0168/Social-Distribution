from django.db import models
import uuid
from django.contrib.auth.models import User
from django.http import HttpRequest  # Import HttpRequest to simulate request.get_host()

class Author(User):
    host = models.CharField(max_length=255, null=False)
    display_name = models.CharField(max_length=100, unique=True)
    github = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.CharField(max_length=255, blank=True, null=True)
    page = models.CharField(max_length=255, blank=True, null=True)
    isVerified = models.BooleanField(default=False)

    USERNAME_FIELD = 'display_name'

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if not self.host:  # Only set if host is not already set
            self.host = f"http://{kwargs.get('request_host', 'localhost')}"
        self.username = self.display_name
        super().save(*args, **kwargs)

