from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework import status
import jwt
from .models import Notification
from rest_framework.decorators import api_view
from author.models import Author, FollowRequest
from posts.models import Post, Comment, Like

@api_view(['GET'])
def inbox(request):
    token = request.COOKIES.get('jwt')
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        payload = jwt.decode(token, 'django-in', algorithms=['HS256'])
        author = get_object_or_404(Author, display_name=payload['id'])

        # Get follow requests sent to the author
        follow_req_notifications = FollowRequest.objects.filter(object_author=author, status='pending')

        # Get posts authored by the author
        posts = Post.objects.filter(author=author)

        # Fetch comments and likes on the author's posts
        comment_notifications = Comment.objects.filter(post__in=posts)
        like_notifications = Like.objects.filter(post__in=posts)

        # Prepare notifications
        notifications = {
            'author': author,
            'follow_requests': follow_req_notifications,
            'comments': comment_notifications,
            'likes': like_notifications
        }

        # Render the template with notifications
        return render(request, 'inbox/inbox.html', notifications)

    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=401)
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid token"}, status=401)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=404)
