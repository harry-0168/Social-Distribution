from django.shortcuts import render, redirect
from django.http import HttpResponse
from posts.models import Post
from author.models import Following
import jwt
from datetime import datetime

def home_page(request):
    '''
    View for the home page
    This view fetches all posts and renders the home page.
    '''
    # Redirect to login if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect('login')

    # Access JWT payload if needed (optional)
    jwt_payload = request.jwt_payload  # Optional
    if jwt_payload:
        author_id = jwt_payload.get('author_id')

    # Fetch all posts, but we will only include posts the user is allowed to see
    all_posts = Post.objects.all().order_by('-published')
    post_list = []

    for post in all_posts:
        # Check if the post is visible to the current user using is_visible_to method
        if post.is_visible_to(request.user):
            is_following = Following.is_following(request.user, post.author) if request.user.is_authenticated else False
            
            # Append post and follow status to the list if visible
            post_list.append({
                'post': post,
                'is_following': is_following
            })

    # Render the home page with posts and follow status
    return render(request, 'home/home_page.html', {
        'post_list': post_list,  # List of posts with follow status
        'author_id': request.user.id,  # The logged-in user's ID
        'display_name': request.user.display_name  # Use display_name instead of username
    })

