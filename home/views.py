from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from posts.models import Post
from posts.serializers import PostSerializer
from author.models import Following, Author
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
import jwt
from datetime import datetime

class PostPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'type': 'posts',
            'page_number': self.page.number,
            'size': self.page.paginator.per_page,
            'count': self.page.paginator.count,
            'src': data,
        })

@api_view(['GET'])
def get_posts(request, author_id):
    """API view to fetch posts"""
    author = get_object_or_404(Author, id=author_id)
    posts = Post.objects.all().order_by('-published')

    paginator = PostPagination()
    result_page = paginator.paginate_queryset(posts, request)

    # Filter posts based on visibility to the current user
    visible_posts = [post for post in result_page if post.is_visible_to(request.user)]
    serializer = PostSerializer(visible_posts, many=True)
    # Adjust the count to reflect only the visible posts
    paginated_response = paginator.get_paginated_response(serializer.data)
    paginated_response.data['count'] = len(visible_posts)

    return paginated_response

def home_page(request):
    '''
    View for the home page
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
    following_list = []

    for post in all_posts:
        # Check if the post is visible to the current user using is_visible_to method
        if post.is_visible_to(request.user):
            is_following = Following.is_following(request.user, post.author) if request.user.is_authenticated else False
            
            # Append post follow status to the list if visible
            following_list.append(is_following)

    # Render the home page with follow status
    return render(request, 'home/home_page.html', {
        'following_list': following_list
    })

