from django.shortcuts import render, redirect
from django.http import HttpResponse
from posts.models import Post
import jwt
from datetime import datetime

def home_page(request):
    token = request.COOKIES.get('jwt')  # Retrieve the JWT token from the cookie
    if not token:
        # Redirect to login if no JWT is present
        return redirect('login')

    try:
        # Assuming your secret key is 'django-in', adjust as per your settings
        payload = jwt.decode(token, 'django-in', algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        # Redirect if the token has expired
        return redirect('login')
    except jwt.DecodeError:
        # Handle invalid token cases by redirecting to login
        return redirect('login')

    author_id = payload.get('author_id')
    if not author_id:
        # Redirect or handle cases where author_id is missing
        return redirect('login')

    posts = Post.objects.filter(visibility='PUBLIC').order_by('-published')
    print("Posts is: ")
    print(author_id)
    print(posts)
    return render(request, 'home/home_page.html', {'posts': posts, 'author_id': author_id})
