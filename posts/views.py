from django.shortcuts import render
from django.views import generic
from .models import Post

# Create your views here.
class CreatePostView(generic.ListView):
    model = Post
    context_object_name = "post"
    template_name = "posts/createPost.html"