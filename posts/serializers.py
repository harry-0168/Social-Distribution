from rest_framework import serializers
from .models import Post, Comment, Like
from author.serializers import AuthorSerializer

class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    class Meta:
        model = Comment
        # specifies which fields to serialize
        fields = ['username', 'published', 'content', 'post', 'author', 'FQID', 'id', 'type', 'contentType']
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        # specifies which fields to serialize
        fields = ['type','username', 'object', 'published','author','id']

class CommentListSerializer(serializers.Serializer):
    type = serializers.CharField(default="comments")
    id = serializers.CharField()
    page = serializers.URLField()
    page_number = serializers.IntegerField(default=1)
    size = serializers.IntegerField()
    count = serializers.IntegerField()
    src = CommentSerializer(many=True, read_only=True)

class LikeListSerializer(serializers.Serializer):
    type = serializers.CharField(default="likes")
    id = serializers.CharField()
    page = serializers.URLField()
    page_number = serializers.IntegerField(default=1)
    size = serializers.IntegerField()
    count = serializers.IntegerField()
    src = LikeSerializer(many=True, read_only=True)

class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True) # So the response actually return the author object instead of just id
    comments = CommentSerializer(many=True, read_only=True)
    class Meta:
        model = Post
        fields = ['id','uuid','type','page', 'title', 'description', 'contentType', 'content', 'visibility', 'author', 'published', 'comments']
    
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
        instance.contentType = validated_data.get('contentType', instance.contentType)
        instance.content = validated_data.get('content', instance.content)
        instance.visibility = validated_data.get('visibility', instance.visibility)
        instance.save()
        return instance