from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest  # Import HttpRequest to simulate request.get_host()

class Author(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.CharField(max_length=255, null=False)
    display_name = models.CharField(_("display_name"),max_length=100, unique=True)
    github = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.CharField(max_length=255, blank=True, null=True)
    page = models.CharField(max_length=255, blank=True, null=True)
    isVerified = models.BooleanField(default=False)
    username = None

    USERNAME_FIELD = 'display_name'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if not self.host:  # Only set if host is not already set
            self.host = f"http://{kwargs.get('request_host', 'localhost')}"
        
        super().save(*args, **kwargs)

