from rest_framework import serializers
from .models import Author, FollowRequest

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'host', 'display_name', 'github', 'profile_image', 'page']

class FollowRequestSerializer(serializers.ModelSerializer):
    actor = AuthorSerializer(read_only=True)
    object_author = AuthorSerializer(read_only=True)

    class Meta:
        model = FollowRequest
        fields = ['id', 'actor', 'object_author', 'summary', 'status']
