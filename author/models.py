from django.db import models

class Author(models.Model):
    host = models.CharField(max_length=255, null=False)
    display_name = models.CharField(max_length=100)
    github = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.CharField(max_length=255, blank=True, null=True)
    page = models.CharField(max_length=255, blank=True, null=True)

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
