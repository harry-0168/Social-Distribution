from datetime import datetime
from django.db import models
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
    # author = models.ForeignKey(Author, related_name='posts', on_delete=models.CASCADE)
    published = models.DateTimeField(auto_now_add=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES)

class Comment(models.Model):
    username = models.CharField(max_length=32) 
    created_at = models.DateTimeField("date created", default=datetime.now)
    content =  models.TextField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE) # all comments belong to a post

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE) # all likes belong to a post
    like_date = models.DateTimeField(default=timezone.now)