from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Author, FollowRequest
from posts.models import Post  
from .serializers import AuthorSerializer, FollowRequestSerializer
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, JsonResponse


def profile_view(request, author_id):
    # Fetch the author by ID
    author = get_object_or_404(Author, id=author_id)
    
    posts = Post.objects.filter(author=author).exclude(visibility='DELETED').order_by('-published')

    # Render the template with the author and posts
    return render(request, 'author/author_feed.html', {
        'author': author,
        'posts': posts
    })

def author_about(request, author_id):
    author = Author.objects.get(id=author_id)  
    return render(request, 'author/author_about.html', {'author': author})

def follow_author(request, author_id):
    if request.method == 'POST':
        user = request.user
        target_author = get_object_or_404(Author, pk=author_id)
        # Check if already following
        if not FollowRequest.objects.filter(actor=user, object_author=target_author).exists():
            FollowRequest.objects.create(actor=user, object_author=target_author, summary=f"{user.display_name} wants to follow {target_author.display_name}", status='accepted')
        return redirect('author_profile', author_id=author_id)

def unfollow_author(request, author_id):
    if request.method == 'DELETE':
        target_author = get_object_or_404(Author, pk=author_id)
        FollowRequest.objects.filter(actor=request.user.author, object_author=target_author).delete()
        return JsonResponse({'message': 'Unfollowed successfully'}, status=204)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def following_list(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    following = FollowRequest.objects.filter(actor=author, status='accepted').select_related('object_author')
    following_count = following.count()
    return render(request, 'author/following_list.html', {'author': author, 'following': following, 'following_count': following_count})

def followers_list(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    followers = FollowRequest.objects.filter(object_author=author, status='accepted').select_related('actor')
    followers_count = followers.count()
    return render(request, 'author/followers_list.html', {'author': author, 'followers': followers, 'followers_count': followers_count})

class AuthorPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 500

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = AuthorPagination

    def send_follow_request(self, request, pk=None):
        # Manually get the object_author using the 'pk' from URL
        try:
            object_author = Author.objects.get(pk=pk)
        except Author.DoesNotExist:
            return Response({"detail": "Object author not found."}, status=status.HTTP_404_NOT_FOUND)

        actor_author_data = request.data.get("actor")
        if not actor_author_data:
            return Response({"detail": "Missing actor data."}, status=status.HTTP_400_BAD_REQUEST)

        # Find the actor author
        try:
            actor_author = Author.objects.get(id=actor_author_data['id'])
        except Author.DoesNotExist:
            return Response({"detail": "Actor author not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create a follow request object
        follow_request = FollowRequest(
            actor=actor_author,
            object_author=object_author,
            summary=f"{actor_author.display_name} wants to follow {object_author.display_name}"
        )
        follow_request.save()

        serializer = FollowRequestSerializer(follow_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def list_inbox(self, request, pk=None):
        # Get the author (object_author) whose inbox we are fetching
        try:
            object_author = Author.objects.get(pk=pk)
        except Author.DoesNotExist:
            return Response({"detail": "Author not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get all follow requests where the current author is the object_author
        follow_requests = FollowRequest.objects.filter(object_author=object_author)
        serializer = FollowRequestSerializer(follow_requests, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
