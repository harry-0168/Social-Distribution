from django.shortcuts import render
from posts.models import Post

def home_page(request):
    posts = Post.objects.all()
    return render(request, 'home/home_page.html', {'posts': posts})