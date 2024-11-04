from rest_framework import serializers
from .models import Post, Comment, Like
from author.serializers import AuthorSerializer

class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True) # So the response actually return the author object instead of just id
    class Meta:
        model = Post
        fields = ['id','type','FQID', 'title', 'description', 'content_type', 'content', 'visibility', 'author', 'published']
    
    def validate_title(self, value):
        if not value:
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value) < 1 or len(value) > 200:
            raise serializers.ValidationError("Title must be between 1 and 200 characters.")
        return value

    def validate_description(self, value):
        if len(value) > 500:
            raise serializers.ValidationError("Description cannot exceed 500 characters.")
        return value

    def create(self, validated_data):
        # Remove author from validated_data as it should be set from the view
        author = validated_data.pop('author', None)
        post = Post.objects.create(**validated_data)
        return post

    def update(self, instance, validated_data):
        # Update instance with the validated data
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.content_type = validated_data.get('content_type', instance.content_type)
        instance.content = validated_data.get('content', instance.content)
        instance.visibility = validated_data.get('visibility', instance.visibility)
        instance.save()
        return instance
    

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        # specifies which fields to serialize
        fields = ['username', 'published', 'content', 'post', 'author', 'FQID', 'id', 'type', 'contentType']



class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        # specifies which fields to serialize
        fields = ['username', 'post', 'like_date']