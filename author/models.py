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
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    page = models.CharField(max_length=255, blank=True, null=True)
    isVerified = models.BooleanField(default=False)
    username = None
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)


    USERNAME_FIELD = 'display_name'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if not self.host:  # Only set if host is not already set
            self.host = f"http://{kwargs.get('request_host', 'localhost')}"
        
        super().save(*args, **kwargs)

# New FollowRequest Model
class FollowRequest(models.Model):
    actor = models.ForeignKey(Author, related_name='follow_requests_sent', on_delete=models.CASCADE)
    object_author = models.ForeignKey(Author, related_name='follow_requests_received', on_delete=models.CASCADE)
    summary = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending')

    def __str__(self):
        return f"{self.actor.display_name} wants to follow {self.object_author.display_name}"
    
class following(models.Model):
    '''Model to store following relationship between authors. author1 is following author2
    this table represents following which is a many to many relationship btw author (author1, author2)
    Exist (a,b) a is following b AND Exist(b,a) b is following a --> friend;  
    Exist(a,b) AND not exist (b,a) --> a is follower of b or b is followed by a
    This is all we need to fetch the relation between authors'''

    author1 = models.ForeignKey(Author, related_name='author', on_delete=models.CASCADE)
    author2 = models.ForeignKey(Author, related_name='following', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.author1.display_name} is following {self.author2.display_name}"
