from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, action,authentication_classes, permission_classes
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
from inbox.models import Inbox
from posts.models import Like
from posts.serializers import LikeSerializer
import json
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated


def profile_view(request, author_id):
    '''
    View to display the public profile of an author
    This view fetches the author by ID and renders the author's profile page.
    '''
    # Fetch the author by ID
    author = get_object_or_404(Author, id=author_id)
    
    # Initialize follow-related variables
    is_following = False
    is_friends = False
    
    # Get follow counts
    followers_count = Following.objects.filter(
        author2=author, 
        status='accepted'  # Only count accepted follows
    ).count()
    
    following_count = Following.objects.filter(
        author1=author, 
        status='accepted'  # Only count accepted follows
    ).count()
    
    # Check relationships if user is authenticated
    if request.user.is_authenticated and request.user != author:
        # Check if following (only if status is accepted)
        is_following = Following.objects.filter(
            author1=request.user, 
            author2=author,
            status='accepted'  # Only consider accepted follows
        ).exists()
        
        # Check if they are friends
        is_friends = Following.are_friends(request.user, author)
    
    # Determine post visibility
    visibility_exclusions = ['DELETED']
    if request.user == author:
        # Author can see all their own posts except deleted ones
        pass
    elif not is_friends and not is_following:
        # Public users can only see public posts
        visibility_exclusions.extend(['FRIENDS', 'UNLISTED'])
    elif not is_friends:
        # Followers can see public and unlisted posts
        visibility_exclusions.append('FRIENDS')

    # Fetch visible posts
    posts = Post.objects.filter(
        author=author
    ).exclude(
        visibility__in=visibility_exclusions
    ).order_by('-published')

    context = {
        'author': author,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
        'is_friends': is_friends,
        'logged_in_user': request.user,
        'is_own_profile': request.user == author
    }
    
    return render(request, 'author/author_feed.html', context)


def author_about(request, author_id):
    '''
    View to display the about page of an author
    This view fetches the author by ID and renders the author's about page.
    '''
    author = Author.objects.get(id=author_id)  
    followers_count = Following.objects.filter(author2=author, status='accepted').count()  # Count of followers
    # Get the Following count (authors this author is Following)
    following_count = Following.objects.filter(author1=author, status='accepted').count()  # Count of people this author is following
    return render(request, 'author/author_about.html', {'author': author, 'followers_count': followers_count, 'following_count': following_count})

@api_view(['GET'])
def api_get_like(request, like_fqid):
    """
    Retrieve a single like by its fully qualified ID (LIKE_FQID).
    """
    try:
        # Fetch the Like instance using the LIKE_FQID
        like = Like.objects.get(id=like_fqid)
        
        # Serialize the Like object
        like_data = {
            'id': like.id,
            'username': like.username,
            'post_id': like.object.id,
            'author_id': like.author.id,
            'published': like.published,
            'type': like.type,
        }

        return Response(like_data, status=status.HTTP_200_OK)
    except Like.DoesNotExist:
        return Response({"error": "Like not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([BasicAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_single_like(request, author_serial, like_serial):
    print("Requested Author Serial:", author_serial)
    print("Requested Like Serial:", like_serial)

    # Get the author based on the provided author_serial
    author = get_object_or_404(Author, id=author_serial)

    # Get the specific like by LIKE_SERIAL and ensure it belongs to the author
    like = get_object_or_404(Like, id=like_serial, author=author)

    # Serialize the like object
    like_serializer = LikeSerializer(like)

    # Return the serialized data
    return Response(like_serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([BasicAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_likes_by_author(request, author_serial):
    print("Requested Author Serial:", author_serial)

    # Get the author based on the provided author_serial
    author = get_object_or_404(Author, id=author_serial)

    # Retrieve all likes by the author
    likes = Like.objects.filter(author=author)

    # Create a dictionary to store the latest likes per post
    latest_likes_dict = {}

    for like in likes:
        post_id = like.object.id
        if post_id not in latest_likes_dict:
            latest_likes_dict[post_id] = like
        else:
            # Compare published dates to find the latest like
            if like.published > latest_likes_dict[post_id].published:
                latest_likes_dict[post_id] = like

    # Get the latest likes as a list
    latest_likes = list(latest_likes_dict.values())

    # Serialize the latest likes queryset
    like_serializer = LikeSerializer(latest_likes, many=True)

    # Return the serialized data
    return Response(like_serializer.data, status=status.HTTP_200_OK)


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
    author = get_object_or_404(Author, id=author_id)
    following = Following.objects.filter(author1=author, status='accepted')
    followers = Following.objects.filter(author2=author, status='accepted')
    
    following_with_status = []
    for follow in following:
        followed_user = follow.author2
        is_following = Following.objects.filter(
            author1=request.user,
            author2=followed_user,
            status='accepted'
        ).exists()
        
        # Use the are_friends method
        is_friend = Following.are_friends(author, followed_user)
        
        following_with_status.append({
            'following': followed_user,
            'is_following': is_following,
            'is_friend': is_friend
        })

    # Add the main author's follow status
    main_author_is_following = Following.objects.filter(
        author1=request.user,
        author2=author,
        status='accepted'
    ).exists()

    context = {
        'author': author,
        'following': following_with_status,
        'following_count': following.count(),
        'followers_count': followers.count(),
        'is_following': main_author_is_following  # Add this for the main profile button
    }
    return render(request, 'author/following_list.html', context)

@api_view(['GET'])
def followers_list(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    followers = Following.objects.filter(author2=author, status='accepted')
    following = Following.objects.filter(author1=author, status='accepted')
    
    followers_with_status = []
    for follow in followers:
        follower = follow.author1
        is_following = Following.objects.filter(
            author1=request.user,
            author2=follower,
            status='accepted'
        ).exists()
        
        # Use the are_friends method
        is_friend = Following.are_friends(follower, author)
        
        followers_with_status.append({
            'follower': follower,
            'is_following': is_following,
            'is_friend': is_friend
        })

    # Add the main author's follow status
    main_author_is_following = Following.objects.filter(
        author1=request.user,
        author2=author,
        status='accepted'
    ).exists()

    context = {
        'author': author,
        'followers': followers_with_status,
        'followers_count': followers.count(),
        'following_count': following.count(),
        'is_following': main_author_is_following  # Add this for the main profile button
    }
    return render(request, 'author/followers_list.html', context)


@api_view(['GET','DELETE','PUT'])
def manage_follower(request, author_id, foreign_author_fqid):
    author = get_object_or_404(Author, id=author_id)

    from urllib.parse import unquote
    foreign_author_fqid = unquote(foreign_author_fqid)

    try:
        foreign_author = Author.objects.get(FQID=foreign_author_fqid)
    except Author.DoesNotExist:
        return Response({"detail": "Foreign author not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Handle GET request: Check if foreign author is following the author
    if request.method =='GET':
        is_follower = Following.is_following(foreign_author, author)
        if is_follower:
            follower_data = {
                "type": "author",
                "id": foreign_author_fqid,
                "host": foreign_author.host,
                "displayName": foreign_author.displayName,
                "page": f"{foreign_author.host}/authors/{foreign_author.id}",
                "github": foreign_author.github,
                "profileImage": foreign_author.profileImage.url
            }
            return Response(follower_data, status=status.HTTP_200_OK)
        
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Handle DELETE request: Remove the follower relationship
    elif request.method =='DELETE':
        if Following.is_following(foreign_author, author):
            Following.unfollow(foreign_author, author)
            return Response({"detail": "Follower removed"}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "No follower relationship exists"}, status=status.HTTP_404_NOT_FOUND)
    
    # Handle PUT request: Add a follower relationship
    elif request.method =='PUT':
        new_following = Following.follow(foreign_author, author)
        if new_following:
            follower_data = {
                "type": "author",
                "id": foreign_author_fqid,
                "host": foreign_author.host,
                "displayName": foreign_author.displayName,
                "page": f"{foreign_author.host}/authors/{foreign_author.id}",
                "github": foreign_author.github,
                "profileImage": foreign_author.profileImage.url,
                "message": f"New follower created for author {author.displayName}"
            }
            return Response(follower_data, status=status.HTTP_201_CREATED)
        else:
            return Response({"detail": "Already following"}, status=status.HTTP_200_OK)



@api_view(['GET'])
def api_list_authors(request):
    paginator = AuthorPagination()  # Use the custom pagination class
    authors = Author.objects.all()
    result_page = paginator.paginate_queryset(authors, request)

    # Format author data as per your required structure
    formatted_authors = []
    for author in result_page:
        profile_image_url = author.profileImage.url if author.profileImage else None  # Updated field name
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
@authentication_classes([BasicAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def api_author_detail(request, author_id):
    # GET request to retrieve a single author
    if request.method == 'GET':
        author = get_object_or_404(Author, id=author_id)
        
        # Construct the full ID URL
        full_id_url = f"{request.scheme}://{request.get_host()}/api/authors/{author.id}"
        
        # Use static default image if profileImage has no file
        if author.profileImage and hasattr(author.profileImage, 'url'):
            profileImage_url = author.profileImage.url
        else:
            profileImage_url = f"{request.scheme}://{request.get_host()}/static/avatar.png"  # Default static image path
        
    
        # Get the host with the postfix
        host_with_postfix = f"{request.scheme}://{request.get_host()}/api/"
        
        data = {
            "type": "author",
            "id": full_id_url,
            "host": host_with_postfix,
            "displayName": author.displayName,
            "github": author.github,
            "profileImage": profileImage_url,
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
            profileImage = data.get('profileImage')
            if profileImage:
                author.profileImage = profileImage

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
    return render(request, 'author/login.html')


def user_settings(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    followers_count = Following.objects.filter(author2=author, status='accepted').count()  # Count of followers
    # Get the Following count (authors this author is Following)
    following_count = Following.objects.filter(author1=author, status='accepted').count()  # Count of people this author is following
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES, instance=author)
        new_display_name = form.data.get('displayName')
        if new_display_name and new_display_name != author.displayName:
            if Author.objects.filter(displayName=new_display_name).exclude(id=author.id).exists():
                messages.error(request, 'This display name is already taken. Please choose another.')
                return render(request, 'author/user_settings.html', {
                    'form': form,
                    'author': author,
                    'redirect_url': request.build_absolute_uri(
                        redirect('author_profile', author_id=author.id).url
                    )
                })
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile changes saved successfully!')
            payload = {
                'id': author.displayName,
                'author_id': str(author.id),
                'exp': datetime.now() + timedelta(days=1),  # Token expiration
                'iat': datetime.now()
            }
            newToken = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

            #Redirect and set the new JWT token in a cookie
            response = render(request, 'author/user_settings.html', {
                'form': form,
                'author': author,
                'redirect_url': request.build_absolute_uri(
                    redirect('author_profile', author_id=author.id).url
                )
            })
            response.set_cookie(key=settings.JWT_AUTH_COOKIE, value=newToken, httponly=True)
            return response


    else:
        form = UserSettingsForm(instance=author)

    return render(request, 'author/user_settings.html', {'form': form, 'author': author, 'followers_count': followers_count, 'following_count': following_count})