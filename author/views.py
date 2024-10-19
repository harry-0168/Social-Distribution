from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, action
from .models import Author, FollowRequest
from django.utils import timezone
from inbox.models import Notification 
from posts.models import Post  
from .serializers import AuthorSerializer, FollowRequestSerializer
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, JsonResponse
import jwt
from datetime import datetime, timedelta
from rest_framework.exceptions import AuthenticationFailed  
from .serializers import UserSettingsForm
from django.contrib import messages
from django.conf import settings


def profile_view(request, author_id):
    # Fetch the author by ID
    author = get_object_or_404(Author, id=author_id)
    
    # Get the follower count and following count
    followers_count = author.followers.count()  # Count of followers
    following_count = author.following.count()  # Count of people this author is following (reverse relation)
    
    # Fetch the author's posts
    posts = Post.objects.filter(author=author).exclude(visibility='DELETED').order_by('-published')

    # Check if the logged-in user is following the author (if user is authenticated)
    is_following = False
    if request.user.is_authenticated:
        is_following = author.followers.filter(id=request.user.id).exists()

    # Render the template with the author, posts, follower count, and if the user is following
    return render(request, 'author/author_feed.html', {
        'author': author,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,  # Add this flag to the context
        'logged_in_user': request.user,  # Pass the logged-in user to the template
    })


def author_about(request, author_id):
    author = Author.objects.get(id=author_id)  
    return render(request, 'author/author_about.html', {'author': author})


def follow_author(request, object_author_id):
    actor = request.user  # The currently logged-in user
    target_author = get_object_or_404(Author, id=object_author_id)

    if target_author != actor:
        if target_author.followers.filter(id=actor.id).exists():
            # Unfollow the author if already following
            target_author.followers.remove(actor)
        else:
            # Follow the author if not already following
            target_author.followers.add(actor)

    # Redirect back to the same page (referer)
    return redirect(request.META.get('HTTP_REFERER', '/'))


def unfollow_author(request, object_author_id):
    if request.method == 'POST':
        actor = request.user  # The logged-in user (actor)
        target_author = get_object_or_404(Author, pk=object_author_id)  # The author to be unfollowed
        
        # Remove the logged-in user from the target's followers
        if actor in target_author.followers.all():
            target_author.followers.remove(actor)
        return redirect('author_profile', author_id=object_author_id)  # Redirect to the author's profile or home

    return redirect('home_page')

def following_list(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    following = author.following.all()  # Get all following
    followers_count = author.followers.count()  # Count the followers
    following_count = following.count()  # Count the following
    
    context = {
        'author': author,
        'following': following,
        'followers_count': followers_count,
        'following_count': following_count,
    }
    
    return render(request, 'author/following_list.html', context)

# View to get the list of followers of the given author
def followers_list(request, author_id):
    # Get the target author (author whose followers we want to list)
    author = get_object_or_404(Author, id=author_id)
    
    # Get the followers (authors who follow this author)
    followers = author.followers.all()  # This gives you all the users who follow the author

    # Get the number of followers and following for the current author
    followers_count = followers.count()
    following_count = author.following.count()  # Number of people this author is following

    context = {
        'author': author,
        'followers': followers,
        'followers_count': followers_count,
        'following_count': following_count,
    }

    return render(request, 'author/followers_list.html', context)





class AuthorPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 500

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = AuthorPagination

    @action(detail=False, methods=['POST'], url_path='send-follow-request')
    def send_follow_request(self, request):
        # Step 1: Get the author UUID from the request data
        actor_author_uuid = request.data.get('actor_uuid')
        target_author_uuid = request.data.get('author_uuid')

        # Step 2: Validate the presence of both UUIDs
        if not actor_author_uuid or not target_author_uuid:
            return Response({"detail": "Missing author UUIDs."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Fetch the authors by UUID
        try:
            actor_author = Author.objects.get(id=actor_author_uuid)
            object_author = Author.objects.get(id=target_author_uuid)
        except Author.DoesNotExist:
            return Response({"detail": "One or both authors not found."}, status=status.HTTP_404_NOT_FOUND)

        # Step 4: Check if a follow request already exists
        if FollowRequest.objects.filter(actor=actor_author, object_author=object_author).exists():
            return Response({"detail": "Follow request already sent."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 5: Create a new follow request
        follow_request = FollowRequest(
            actor=actor_author,
            object_author=object_author,
            summary=f"{actor_author.display_name} wants to follow {object_author.display_name}",
            status='pending'  # Initial status set to 'pending'
        )
        
        follow_request.save()
        """

        # Step 6: Create a notification for the target author
        notification = Notification(
            author=object_author,
            type='follow',  # Set type to 'follow' for follow requests
            post=None,  # No post associated with this notification
            received_at=timezone.now()
        )
        notification.save()
        """
        


        # Step 6: Return the created follow request
        serializer = FollowRequestSerializer(follow_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



##########
''' Code for Author authentication/ Login to our website 
    https://www.youtube.com/watch?v=PUzgZrS_piQ
'''
@api_view(['POST'])
def login(request):
    author = get_object_or_404(Author, display_name=request.data['display_name'])
    if not author.isVerified:
        return Response({"detail": "Not Verified by admin"}, status=status.HTTP_401_UNAUTHORIZED)
    if not author.check_password(request.data['password']):
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    # Generate the JWT token
    payload = {
        'id': author.display_name,
        'author_id': str(author.id),
        'exp': datetime.now() + timedelta(days=1),  # Token expiration
        'iat': datetime.now()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    # Set the JWT token in a cookie
    response = Response({"detail": "Login successful"})
    response.set_cookie(key=settings.JWT_AUTH_COOKIE, value=token, httponly=True)
    
    return response

@api_view(['POST'])
def signup(request):
    serializer = AuthorSerializer(data = request.data, partial= True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status= status.HTTP_201_CREATED)

    return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_author_from_cookie(request):
    token = request.COOKIES.get('jwt')
    if not token:
        return AuthenticationFailed("Unauthenticated")
    
    try:
        payload = jwt.decode(token, 'django-in', algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return AuthenticationFailed("Unauthenticated")
    
    author = Author.objects.filter(display_name = payload['id']).first()
    serializer = AuthorSerializer(instance = author)
    return Response(serializer.data)

@api_view(['POST'])
def logout(request):
    response = Response()
    response.delete_cookie('jwt')
    response.data = {
        "message": "success"
    }
    return response


def user_settings(request, author_id):
    author = get_object_or_404(Author, id=author_id)

    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES, instance=author)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile changes saved successfully!')
            # Pass the redirect URL to the template
            return render(request, 'author/user_settings.html', {
                'form': form,
                'author': author,
                'redirect_url': request.build_absolute_uri(
                    redirect('author_profile', author_id=author.id).url
                )
            })

    else:
        form = UserSettingsForm(instance=author)

    return render(request, 'author/user_settings.html', {'form': form, 'author': author})