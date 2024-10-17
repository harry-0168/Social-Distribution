from django.contrib import admin
from .models import Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published', 'visibility')

    # Overriding the delete_model function to mark the post as deleted
    def delete_model(self, request, obj):
        obj.visibility = 'DELETED'  # Set visibility to DELETED
        obj.save()  # Save the post without actually deleting it

    # Overriding the delete_queryset function to mark multiple posts as deleted
    def delete_queryset(self, request, queryset):
        queryset.update(visibility='DELETED')
        
        
admin.site.register(Post, PostAdmin)
