from django.shortcuts import render, redirect
from django.http import HttpResponse
from posts.models import Post
import jwt
from datetime import datetime

def home_page(request):
    # The user is automatically set by the middleware
    if not request.user.is_authenticated:
        return redirect('login')

    # You can also access JWT payload if needed
    jwt_payload = request.jwt_payload  # Optional

    # For example, extracting more fields from the payload
    if jwt_payload:
        author_id = jwt_payload.get('author_id')
        # You can use author_id if needed

    posts = Post.objects.filter(visibility='PUBLIC').order_by('-published')
    return render(request, 'home/home_page.html', {
        'posts': posts, 
        'author_id': request.user.id,  # Now you can get the user ID
        'username': request.user.username  # Use the authenticated username
    })

