from django.db import models

class Node(models.Model):
    base_url = models.URLField(unique=True)
    access_token = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, choices=[('accepted', 'Accepted'), ('rejected', 'Rejected')], default='accepted')

    def __str__(self):
        return self.base_url
