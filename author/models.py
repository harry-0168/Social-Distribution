from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest  # Import HttpRequest to simulate request.get_host()
from django.utils import timezone
class Author(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    FQID = models.CharField(max_length= 1000, unique=True, null=True)
    host = models.CharField(max_length=255, null=False)
    display_name = models.CharField(_("display_name"),max_length=100, unique=True)
    github = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    page = models.CharField( max_length=1000,blank=True, null=True)
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
        if not self.FQID:  # Only set if FQID is not already set
            self.FQID = f"{self.host}/api/authors/{self.id}"
        if not self.page:
            self.page = f"{self.host}/authors/{self.display_name}"
        
        super().save(*args, **kwargs)

# New FollowRequest Model
class FollowRequest(models.Model):
    actor = models.ForeignKey(Author, related_name='follow_requests_sent', on_delete=models.CASCADE)
    object_author = models.ForeignKey(Author, related_name='follow_requests_received', on_delete=models.CASCADE)
    summary = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending')

    def __str__(self):
        return f"{self.actor.display_name} wants to follow {self.object_author.display_name}"
    
class Following(models.Model):
    '''Model to store following relationship between authors. author1 is following author2
    this table represents following which is a many to many relationship btw author (author1, author2)
    Exist (a,b) a is following b AND Exist(b,a) b is following a --> friend;  
    Exist(a,b) AND not exist (b,a) --> a is follower of b or b is followed by a
    This is all we need to fetch the relation between authors'''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author1 = models.ForeignKey(Author, related_name='author', on_delete=models.CASCADE)
    author2 = models.ForeignKey(Author, related_name='following', on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.author1.display_name} is following {self.author2.display_name}"

    @staticmethod
    def is_following(author1, author2):
        """Check if author1 is following author2."""
        return Following.objects.filter(author1=author1, author2=author2).exists()

    @staticmethod
    def are_friends(author1, author2):
        """Check if both authors are following each other (mutual following)."""
        return (Following.objects.filter(author1=author1, author2=author2).exists() and
                Following.objects.filter(author1=author2, author2=author1).exists())
        
    @staticmethod
    def follow(author1, author2):
        """Follow an author."""
        new = None  # if new following relationship is created return it else return None
        if not Following.objects.filter(author1=author1, author2=author2).exists():
            new = Following.objects.create(author1=author1, author2=author2)
        return new
        
        

    @staticmethod
    def unfollow(author1, author2):
        """Unfollow an author and potentially unfriend."""
        Following.objects.filter(author1=author1, author2=author2).delete()
