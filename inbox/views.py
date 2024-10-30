from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.response import Response
from rest_framework import status
import jwt
from django.conf import settings
from .models import Notification
from rest_framework.decorators import api_view
from author.models import Author, FollowRequest
from posts.models import Post, Comment, Like
from django.conf import settings
import json
from author.models import Following
from .models import Inbox
from django.utils import timezone

@api_view(['GET'])
def inbox(request):
    token = request.COOKIES.get('jwt')
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        author = get_object_or_404(Author, display_name=payload['id']) # author that sent the request

        # Get follow requests, comments, and likes as querysets
        follow_req_notifications = Following.objects.filter(author2=author, status='pending')
        posts = Post.objects.filter(author=author)
        comment_notifications = Comment.objects.filter(post__in=posts)
        like_notifications = Like.objects.filter(post__in=posts)
        
        # Get the list of authors that the current user is following
        followed_authors = Following.objects.filter(author1=author).values_list('author2', flat=True)
        # Filter for repost notifications where the author is in the list of followed authors
        repost_notifications = Post.objects.filter(author__in=followed_authors, type="repost")

        # Serialize the querysets to JSON-serializable data
        follow_requests_data = list(follow_req_notifications.values('id', 'author1__display_name', 'author2__display_name','date'))
        comment_data = list(comment_notifications.values('id', 'username', 'content', 'created_at', 'post__title'))
        like_data = list(like_notifications.values('id', 'username', 'post__title', 'like_date'))
        repost_data = list(repost_notifications.values('id', 'author__display_name', 'content', 'title'))

        # Send the data to the template
        context = {
            'follow_requests': follow_requests_data,
            'comments': comment_data,
            'likes': like_data,
            'reposts': repost_data
        }

        return render(request, 'inbox/inbox.html', context)

    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=401)
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid token"}, status=401)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=404)
    
@api_view(['POST'])
def inboxApi(request, object_author_id):
    token = request.COOKIES.get('jwt')
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        author = get_object_or_404(Author, display_name=payload['id']) # author that sent the request

        # Parse JSON string into a Python dictionary
        parsed_data = request.data

        # check the type of request object
        if parsed_data['type'] == 'follow':
            try:
                actor = get_object_or_404(Author, FQID=parsed_data['actor']['id'])
                object_author = get_object_or_404(Author, FQID=parsed_data['object']['id'])
                # check if the actor is already following the object_author
                if actor.FQID == object_author.FQID:
                    return Response({"error": "Cannot follow yourself"}, status=400)
                new = Following.follow(actor, object_author)
                if not new:
                    return Response({"error": "Already following"}, status=400)
                
                inboxxx = Inbox(receiver=object_author, type='follow', FQIDorId=new.id, received_at=timezone.now()).save()

                return Response({"message": "Follow request sent","requestStatus":new.status}, status=200)


            
            except Author.DoesNotExist:
                # forward the request to the next host server if host is not the current host
                # if actor does not exist create it and send a follow request to the object_author
                # if object_author does not exist forward the request to the next host server inbox
                return Response({"error": "Actor not found"}, status=404)
    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=401)
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid token"}, status=401)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=404)
    
@api_view(['POST'])
def handle_follow_request_response(request):
    token = request.COOKIES.get('jwt')
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        author = get_object_or_404(Author, display_name=payload['id']) # author that sent the request

        # Parse JSON string into a Python dictionary
        parsed_data = request.data
        if parsed_data['status'] == 'accept':
            follow_request = get_object_or_404(Following, id=parsed_data['id'])
            follow_request.status = 'accepted'
            follow_request.save()
            return Response({"message": "Follow request accepted"}, status=200)
        elif parsed_data['status'] == 'reject':
            follow_request = get_object_or_404(Following, id=parsed_data['id'])
            follow_request.delete()
            return Response({"message": "Follow request rejected"}, status=200)
        
    except jwt.ExpiredSignatureError: # redirect to /login
        return redirect('login')

