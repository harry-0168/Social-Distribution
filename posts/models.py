from datetime import datetime
from django.db import models
from author.models import Author, Following
from django.utils import timezone
import uuid

VISIBILITY_CHOICES = [
    ('PUBLIC', 'Public'),
    ('FRIENDS', 'Friends'),
    ('UNLISTED', 'Unlisted'),
    ('DELETED', 'Deleted')
]

CONTENT_TYPE_CHOICES = [
    ('text/markdown', 'Markdown'),
    ('text/plain', 'Plain Text'),
    ('application/base64', 'Base64 Image'),
    ('image/png;base64', 'PNG Image'),
    ('image/jpeg;base64', 'JPEG Image')
]

# Create your models here.
class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    content_type = models.CharField(max_length=100, choices=CONTENT_TYPE_CHOICES)
    content = models.TextField()
    author = models.ForeignKey(Author, related_name='posts', on_delete=models.CASCADE)
    published = models.DateTimeField(auto_now_add=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES)
    FQID = models.CharField(max_length=1000, unique=True, null=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Ensure FQID is set on creation only
        if not self.FQID:
            # Assumes the host is accessible in kwargs;
            host = kwargs.get('request_host', 'localhost')
            self.FQID = f"http://{host}/api/posts/{self.id}"
        
        super().save(*args, **kwargs)
    
    def is_visible_to(self, user):
        """Determine if the current post is visible to the specified user."""
        # Deleted posts should not be visible to anyone except admins
        if self.visibility == 'DELETED':
            return False

        # Public posts are visible to everyone
        if self.visibility == 'PUBLIC':
            return True

        # Unlisted posts are visible only to logged-in users with a link
        if self.visibility == 'UNLISTED':
            return Following.is_following(user, self.author) or user == self.author

        # Friends-only posts are visible to friends (mutual followers)
        if self.visibility == 'FRIENDS':
            return Following.are_friends(self.author, user)

        # By default, the post is not visible
        return False

class Comment(models.Model):
    username = models.CharField(max_length=32) 
    published = models.DateTimeField("date created", default=timezone.now) 
    content =  models.TextField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE) # all comments belong to a post
    author = models.ForeignKey(Author, related_name='comments', on_delete=models.CASCADE)
    FQID = models.CharField(max_length=1000, unique=True, null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20)
    contentType = "text/markdown"
    #likes

    def save(self, *args, **kwargs):
        ''' Override the save method to set the FQID field before saving '''
        if not self.FQID:  # Only set if FQID is not already set
            host = kwargs.get('request_host', 'localhost')
            self.FQID = f"http://{host}/api/comments/{self.id}"
        
        super().save(*args, **kwargs)

class Like(models.Model):
    username = models.CharField(max_length=255,default="1")  # Store the display name instead of Author object
    post = models.ForeignKey(Post, on_delete=models.CASCADE)  # All likes belong to a post  TODO: REFACTOR to "object"
    like_date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(Author, related_name='likes', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.username} liked {self.post.title}"
    
