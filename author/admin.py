from django.contrib import admin
from .models import Author, following


admin.site.register(Author)

admin.site.register(following)