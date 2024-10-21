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
    # id = models.CharField(primary_key=True, unique=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    content_type = models.CharField(max_length=100, choices=CONTENT_TYPE_CHOICES)
    content = models.TextField()
    author = models.ForeignKey(Author, related_name='posts', on_delete=models.CASCADE)
    published = models.DateTimeField(auto_now_add=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES)
    
    def __str__(self):
        return self.title
    
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
            return user.is_authenticated

        # Friends-only posts are visible to friends (mutual followers)
        if self.visibility == 'FRIENDS':
            return Following.are_friends(self.author, user)

        # By default, the post is not visible
        return False

class Comment(models.Model):
    username = models.CharField(max_length=32) 
    created_at = models.DateTimeField("date created", default=timezone.now)
    content =  models.TextField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE) # all comments belong to a post
    author = models.ForeignKey(Author, related_name='comments', on_delete=models.CASCADE)

class Like(models.Model):
    username = models.CharField(max_length=255,default="1")  # Store the display name instead of Author object
    post = models.ForeignKey(Post, on_delete=models.CASCADE)  # All likes belong to a post
    like_date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(Author, related_name='likes', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.username} liked {self.post.title}"
    
