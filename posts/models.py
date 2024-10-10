from django.db import models
from datetime import datetime

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
    id = models.URLField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES)
    content = models.TextField()
    # author = models.ForeignKey(Author, related_name='posts', on_delete=models.CASCADE)
    published = models.DateTimeField(default=datetime.now)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES)