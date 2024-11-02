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
from django.http import Http404, JsonResponse, HttpResponse, HttpResponseNotFound
import jwt
from datetime import datetime, timedelta
from rest_framework.exceptions import AuthenticationFailed  
from .serializers import UserSettingsForm
from django.contrib import messages
from django.conf import settings
from .models import Author, Following
import json


def profile_view(request, author_id):
    '''
    View to display the public profile of an author
    This view fetches the author by ID and renders the author's profile page.
    '''
    # Fetch the author by ID
    author = get_object_or_404(Author, id=author_id)
    
    # Get the follower count (authors who follow this author)
    followers_count = Following.objects.filter(author2=author).count()  # Count of followers
    
    # Get the Following count (authors this author is Following)
    following_count = Following.objects.filter(author1=author).count()  # Count of people this author is following
    
    # Fetch the author's posts
    posts = Post.objects.filter(author=author).exclude(visibility='DELETED').order_by('-published')

    # Check if the logged-in user is following the author (if user is authenticated)
    is_following = False
    if request.user.is_authenticated:
        is_following = Following.objects.filter(author1=request.user, author2=author).exists()

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
    '''
    View to display the about page of an author
    This view fetches the author by ID and renders the author's about page.
    '''
    author = Author.objects.get(id=author_id)  
    return render(request, 'author/author_about.html', {'author': author})


def follow_author(request, object_author_id):
    '''
    This view is used to follow the target author. It fetches the currently logged-in user and the target author.
    It then follows the target author using the follow method in the model.
    '''
    """Follow the target author."""
    if request.method == 'POST' and request.user.is_authenticated:
        actor = request.user  # The currently logged-in user
        target_author = get_object_or_404(Author, id=object_author_id)  # The author to be followed

        # Prevent users from following themselves
        if target_author != actor:
            # Follow the target author using the follow method in the model
            Following.follow(actor, target_author)
        
        # Optionally, check if they are now mutual followers (friends)
        if Following.are_friends(actor, target_author):
            message = f"You are now friends with {target_author.displayName}."
        
        # Redirect back to the referring page
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('home_page')


def unfollow_author(request, object_author_id):
    '''
    This view is used to unfollow the target author. It fetches the currently logged-in user and the target author.
    It then unfollows the target author using the unfollow method in the model.
    '''
    """Unfollow the target author."""
    if request.method == 'POST' and request.user.is_authenticated:
        actor = request.user  # The currently logged-in user
        target_author = get_object_or_404(Author, id=object_author_id)  # The author to be unfollowed

        # Prevent users from unfollowing themselves
        if target_author != actor:
            # Unfollow the target author using the unfollow method in the model
            Following.unfollow(actor, target_author)

        # Redirect back to the referring page
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('home_page')

def following_list(request, author_id):
    '''
    View to get the list of authors that the given author is following
    This view fetches the target author and lists all authors that the target author is following.
    '''
    author = get_object_or_404(Author, id=author_id)
    
    # Get all authors that the current author is following
    follow_relationships = Following.objects.filter(author1=author).select_related('author2')

    context = {
        'author': author,
        'following': [rel.author2 for rel in follow_relationships],  # List of authors being followed
        'followers_count': Following.objects.filter(author2=author).count(),  # Count of followers
        'following_count': follow_relationships.count(),  # Count of following
    }

    return render(request, 'author/following_list.html', context)

# View to get the list of followers of the given author
def followers_list(request, author_id):
    '''
    View to get the list of authors that follow the given author
    This view fetches the target author and lists all authors that follow the target author.
    '''
    # Get the target author (author whose followers we want to list)
    author = get_object_or_404(Author, id=author_id)
    
    # Get all authors who follow this author
    followers = Following.objects.filter(author2=author).select_related('author1')

    context = {
        'author': author,
        'followers': [rel.author1 for rel in followers],  # List of authors who follow the target
        'followers_count': followers.count(),  # Number of followers
        'following_count': Following.objects.filter(author1=author).count(),  # Number of authors this user is following
    }

    return render(request, 'author/followers_list.html', context)

@api_view(['GET'])
def api_list_authors(request):
    paginator = AuthorPagination()  # Use the custom pagination class
    authors = Author.objects.all()
    result_page = paginator.paginate_queryset(authors, request)

    # Format author data as per your required structure
    formatted_authors = []
    for author in result_page:
        profile_image_url = author.profile_image.url if author.profile_image else None
        full_id_url = f"{request.scheme}://{request.get_host()}/api/authors/{author.id}"
        host_with_postfix = f"{request.scheme}://{request.get_host()}/api/"

        formatted_authors.append({
            "type": "author",
            "id": full_id_url,
            "host": host_with_postfix,
            "displayName": author.displayName,
            "github": author.github,
            "profileImage": profile_image_url,
            "page": author.page,
        })

    # Return the customized paginated response
    return paginator.get_paginated_response(formatted_authors)
    
    
@api_view(['POST'])
def api_add_author(request):
    # Deserialize the incoming request data using the AuthorSerializer
    serializer = AuthorSerializer(data=request.data)

    # Validate and save the data if it's valid
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Author created successfully", "author": serializer.data}, status=status.HTTP_201_CREATED)

    # If data is invalid, return the errors
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET', 'PUT'])
def api_author_detail(request, author_id):
    # GET request to retrieve a single author
    if request.method == 'GET':
        author = get_object_or_404(Author, id=author_id)
        
        # Construct the full ID URL
        full_id_url = f"{request.scheme}://{request.get_host()}/api/authors/{author.id}"
        
        # Handle the serialization of ImageField (use URL or None if not available)
        profile_image_url = author.profile_image.url if author.profile_image else None

        # Get the host with the postfix
        host_with_postfix = f"{request.scheme}://{request.get_host()}/api/"
        
        data = {
            "type": "author",
            "id": full_id_url,
            "host": host_with_postfix,
            "displayName": author.displayName,
            "github": author.github,
            "profile_image": profile_image_url,
            "page": author.page,
        }
        return Response(data, status=status.HTTP_200_OK)
    
    # PUT request to modify an author
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)

            author = get_object_or_404(Author, id=author_id)

            author.displayName = data.get('displayName', author.displayName)
            author.github = data.get('github', author.github)
            author.page = data.get('page', author.page)

            # Handle image update - in PUT requests, this typically requires a multipart form-data request
            profile_image = data.get('profile_image')
            if profile_image:
                author.profile_image = profile_image

            author.save()

            return Response({'message': 'Author modified successfully'}, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON data'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HttpResponseNotFound()
    





class AuthorPagination(PageNumberPagination):
    page_size = 100 # Default number of items per page
    page_size_query_param = 'size' # Custom query parameter for page size
    max_page_size = 1000 # Maximum number of items per page

    def get_paginated_response(self, data):
        # Customize the response format to only include `type` and `authors`
        return Response({
            "type": "authors",
            "authors": data
        })

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
            summary=f"{actor_author.displayName} wants to follow {object_author.displayName}",
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
def loginPage(request):
    return render(request, 'author/login.html')


@api_view(['POST'])
def login(request):
    author = get_object_or_404(Author, displayName=request.data['displayName'])
    if not author.isVerified:
        return Response({"detail": "Not Verified by admin"}, status=status.HTTP_401_UNAUTHORIZED)
    if not author.check_password(request.data['password']):
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    # Generate the JWT token
    payload = {
        'id': author.displayName,
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

    return Response({"detail": "UserName already exists."}, status= status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_author_from_cookie(request):
    token = request.COOKIES.get('jwt')
    if not token:
        return AuthenticationFailed("Unauthenticated")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return AuthenticationFailed("Unauthenticated")
    
    author = Author.objects.filter(displayName = payload['id']).first()
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