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
''' Code for Author authentication/ Login to our website '''
@api_view(['POST'])
def login(request):
    author = get_object_or_404(Author, display_name = request.data['display_name'])
    if not author.isVerified:
        return Response({"detail":"Not Verified by admin"}, status= status.HTTP_401_UNAUTHORIZED)
    if not author.check_password(request.data['password']):
        return Response({"detail":"Not found"}, status= status.HTTP_404_NOT_FOUND)
    # token, created = Token.objects.get_or_create(user = author)
    payload = {
        'id': author.display_name,
        'exp': datetime.now() + timedelta(days=1),
        'iat': datetime.now()
    }
    SECRET_KEY = 'django-in'
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    serializer = AuthorSerializer(instance = author)
    response = Response()
    response.set_cookie(key='jwt', value=token, httponly=True)  
    response.data= {"jwt":token,"author":serializer.data}
    this_user=author.id
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