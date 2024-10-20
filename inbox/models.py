from django.db import models
from author.models import Author
from posts.models import Post

# Create your models here.
INBOX_ENTRY_TYPE_CHOICES = [
    ('shared_post', 'Shared Post'),
    ('follow', 'Follow Request'),
    ('like', 'Like'),
    ('comment', 'Comment'),
]

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    author = models.ForeignKey(Author, related_name='inbox', on_delete=models.CASCADE)
    type = models.CharField(max_length=11, choices=INBOX_ENTRY_TYPE_CHOICES)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.SET_NULL)
    # follow_request = models.ForeignKey(Authors, null=True, blank=True, on_delete=models.SET_NULL)
    received_at = models.DateTimeField()