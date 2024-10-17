from rest_framework import serializers
from .models import Author

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'host', 'display_name', 'github', 'profile_image', 'page', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    
    # def update(self, instance, validated_data):
    #     instance.choice_text = validated_data.get('choice_text', instance.choice_text)
    #     instance.question = validated_data.get('question', instance.question)
    #     instance.votes = validated_data.get('votes', instance.votes)
    #     instance.save()
    #     return instance


