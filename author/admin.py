from django.contrib import admin
from .models import Author, following

# Register models 
admin.site.register(Author)
admin.site.register(following)