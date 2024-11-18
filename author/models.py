from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest  # Import HttpRequest to simulate request.get_host()
from django.utils import timezone
class Author(AbstractUser):
    '''
    Custom User model to represent an author in the system
    The model extends the AbstractUser model and overrides the username field with displayName
    '''
    # set type to author and make it read only
    TYPE_CHOICES = [("author", "Author"), ("node", "Node")]
    
    # New field to differentiate between author and node
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="author")
    author_serial = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.CharField(max_length= 1000, unique=True, null=True)
    host = models.CharField(max_length=255, null=False)
    displayName = models.CharField(_("displayName"),max_length=100, unique=True)
    github = models.CharField(max_length=255, blank=True, null=True)
    profileImage = models.TextField(blank=True, null=True) 
    page = models.CharField( max_length=1000,blank=True, null=True)
    isVerified = models.BooleanField(default=False)
    isNode = models.BooleanField(default=False)
    username = None


    USERNAME_FIELD = 'displayName'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.displayName

    def save(self, *args, **kwargs):
        '''
        Override the save method to set the host field if not already set
        '''
        Default_profile_image_BASE64 = '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'
        request = kwargs.pop('request', None)
    
        if not self.host and request:
            # Use the request object to determine the scheme (http or https)
            scheme = request.scheme
            host = request.get_host()
            print(scheme, host)
            self.host = f"{scheme}://{host}"
        elif not self.host:
            # Fallback if no request object is provided
            self.host = "http://localhost"

        if not self.id:  # Set the id if not already set
            self.id = f"{self.host}/api/authors/{self.author_serial}"

        if not self.profileImage:
            self.profileImage = Default_profile_image_BASE64

        if not self.page:
            self.page = f"{self.host}/authors/{self.displayName}"

        super().save(*args, **kwargs)
        
    def is_friend(self, other_author):
        """ Check if there is a mutual following relationship with another author, indicating friendship. """
        return Following.are_friends(self, other_author)

# New FollowRequest Model
class FollowRequest(models.Model):
    actor = models.ForeignKey(Author, related_name='follow_requests_sent', on_delete=models.CASCADE)
    object_author = models.ForeignKey(Author, related_name='follow_requests_received', on_delete=models.CASCADE)
    summary = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending')

    def __str__(self):
        return f"{self.actor.displayName} wants to follow {self.object_author.displayName}"
    
class Following(models.Model):
    '''Model to store following relationship between authors. author1 is following author2
    this table represents following which is a many to many relationship btw author (author1, author2)
    Exist (a,b) a is following b AND Exist(b,a) b is following a --> friend;  
    Exist(a,b) AND not exist (b,a) --> a is follower of b or b is followed by a
    This is all we need to fetch the relation between authors'''

    type = "follow"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author1 = models.ForeignKey(Author, related_name='author', on_delete=models.CASCADE) # actor
    author2 = models.ForeignKey(Author, related_name='following', on_delete=models.CASCADE) # object
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.author1.displayName} is following {self.author2.displayName}"

    @staticmethod
    def is_following(author1, author2):
        """Check if author1 is following author2."""
        return Following.objects.filter(author1=author1, author2=author2, status='accepted').exists()

    @staticmethod
    def are_friends(author1, author2):
        """Check if both authors are following each other (mutual following)."""
        return (Following.objects.filter(author1=author1, author2=author2, status="accepted").exists() and
            Following.objects.filter(author1=author2, author2=author1, status="accepted").exists())
        
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
    
    @staticmethod
    def get_followers(author):
        """Get all authors following an author."""
        return Following.objects.filter(author2=author, status='accepted')
    
    @staticmethod
    def get_following(author):
        """Get all authors an author is following."""
        return Following.objects.filter(author1=author, status='accepted')
