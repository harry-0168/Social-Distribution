from rest_framework import serializers
from .models import Author
from django import forms

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'host', 'display_name', 'github', 'profile_image', 'page']
class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['display_name', 'github', 'profile_image']
        widgets = {
            'profile_image': forms.FileInput(),
        }