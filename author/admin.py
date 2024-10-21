from django.contrib import admin
from .models import Author, Following

# Register models 
admin.site.register(Author)

admin.site.register(Following)