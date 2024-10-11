from django.db import models

class Author(models.Model):
    id = models.URLField(primary_key=True)
    host = models.URLField()
    display_name = models.CharField(max_length=100)
    github = models.URLField(blank=True, null=True)
    profile_image = models.URLField(blank=True, null=True)
    page = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.display_name
    
   