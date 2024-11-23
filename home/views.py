from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from posts.models import Post
from author.models import Following
from django.utils.safestring import mark_safe
import json

def home_page(request):
    '''
    View for the home page
    '''
    # Redirect to login if the user is not authenticated
    if not request.user.is_authenticated:
        return redirect('loginPage')

    # Fetch all posts, but we will only include posts the user is allowed to see
    all_posts = Post.objects.all().order_by('-published')
    visible_posts = []

    for post in all_posts:
        # Check if the post is visible to the current user using is_visible_to method
        if post.is_visible_to(request.user):
            # Handle profileImage - use the base64 string directly
            profile_image = post.author.profileImage
            
            visible_posts.append({
                'id': str(post.id),
                'title': post.title,
                'description': post.description,
                'content': post.content,
                'contentType': post.contentType,
                'author': {
                    'id': str(post.author.id),
                    'displayName': post.author.displayName,
                    'profileImage': profile_image,  # Just pass the base64 string directly
                },
                'published': post.published.isoformat(),
                'visibility': post.visibility,
            })

    # Render the home page with the visible posts
    return render(request, 'home/home_page.html', {
        'posts': mark_safe(json.dumps(visible_posts)),
    })

