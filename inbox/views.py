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
        author = get_object_or_404(Author, displayName=payload['id']) # author that sent the request

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
        
        follow_requests_data = list(follow_req_notifications.values('id', 'author1__FQID', 'author2__FQID', 'author1__displayName','author1__profileImage','date'))
        comment_data = list(comment_notifications.values('id', 'username', 'content', 'published', 'post__title', 'author__profileImage', 'author__displayName'))
        like_data = list(like_notifications.values('id', 'username', 'post__title', 'like_date', 'author__displayName', 'author__profileImage'))
        repost_data = list(repost_notifications.values('id', 'author__displayName', 'content', 'title', 'author__profileImage'))

        # Send the data to the template
        for follow_request in follow_requests_data:
            follow_request['author1__profileImage'] = author.host + settings.MEDIA_URL +follow_request['author1__profileImage']
        
        for comment in comment_data:
            comment['author__profileImage'] = author.host + settings.MEDIA_URL + comment['author__profileImage']
        
        for like in like_data:
            like['author__profileImage'] = author.host + settings.MEDIA_URL + like['author__profileImage']

        for repost in repost_data:
            repost['author__profileImage'] = author.host + settings.MEDIA_URL + repost['author__profileImage']
        
        print(repost_data)
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
        # redirect to login page
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED) 
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        author = get_object_or_404(Author, displayName=payload['id']) # author that sent the request

        # Parse JSON string into a Python dictionary
        parsed_data = request.data

        # check the type of request object
        if parsed_data['type'] == 'follow':
            try:
                print(parsed_data['actor']['id'], author.FQID)
                if author.FQID != parsed_data['actor']['id']:
                    return Response({"error": "Invalid request"}, status=401)
                if parsed_data['object']['host'] != parsed_data['actor']['host']:
                    # create object author and following object, then forward the request to the next host server
                    AuthorSerializer = AuthorSerializer(id=parsed_data['object']['id'], host=parsed_data['object']['host'], displayName=parsed_data['object']['displayName'], github=parsed_data['object']['github'], profileImage=parsed_data['object']['profileImage'], page=parsed_data['object']['url'])
                    if AuthorSerializer.is_valid():
                        AuthorSerializer.save()
                    else:
                        return Response({"error": "Invalid object author data"}, status=400)
                    object_author = Author.objects.get(id=parsed_data['object']['id'])
                    if not Following.follow(actor, object_author):
                        return Response({"error": "Already following"}, status=400)
                    return Response({"error": "Forwarding request to the next host server"}, status=200)
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
            
        elif parsed_data['type'] == 'comment':
            object_author = Author.objects.get(id=parsed_data['object']['post']['author'])
            Inbox(receiver=object_author, type='comment', FQIDorId=parsed_data['object']['FQID'], received_at=timezone.now()).save()
            return Response({"message": "Comment sent"}, status=200)

    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=401)
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid token"}, status=401)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=404)
    
@api_view(['GET', 'DELETE', 'PUT'])
def handle_follow_request_response(request, author_id, foreign_author_fqid):
    token = request.COOKIES.get('jwt')
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        author = get_object_or_404(Author, displayName=payload['id']) # author that sent the request
        if author.id != author_id:
            return Response({"error": "Unauthorized"}, status=401)
        
        # foreign_author_fqid will be percent encoded, so we need to decode it
        foreign_author_fqid = foreign_author_fqid.replace('%2F', '/')
        foreign_author_fqid = foreign_author_fqid.replace('%3A', ':')
        
        foreign_author = get_object_or_404(Author, FQID=foreign_author_fqid)
        if request.method == 'PUT':
            # Accept follow request from foreign_author 
            follow_request = get_object_or_404(Following, author1 = foreign_author, author2 = author, status='pending')
            follow_request.status = 'accepted'
            follow_request.save()
            return Response({"message": "Follow request accepted"}, status=200)
        elif request.method == 'DELETE':
            # Reject follow request from foreign_authorm, status can be 'pending' or 'accepted'
            follow_request = get_object_or_404(Following, author1 = foreign_author, author2 = author)
            follow_request.delete()
            return Response({"message": "Follow request rejected"}, status=200)
        elif request.method == 'GET':
            # Get the follow request from foreign_author
            # check if FOREIGN_AUTHOR_FQID is a follower of AUTHOR_SERIAL Should return 404 if they're not.This is how you can check if follow request is accepted
            follow_request = get_object_or_404(Following, author1 = foreign_author, author2 = author, status='accepted')
            return Response({"message": "Follow request accepted"}, status=200)
    except jwt.ExpiredSignatureError: # redirect to /login
        return redirect('login')

    except jwt.InvalidTokenError: # redirect to /login
        return redirect('login')

@api_view(['GET'])
def get_followers(request, author_id):
    ''' example response
    {
    "type": "followers",      
    "followers":[
        {
            "type":"author",
            "id":"http://nodebbbb/api/authors/222",
            "host":"http://nodebbbb/api/",
            "displayName":"Lara Croft",
            "page":"http://nodebbbb/authors/222",
            "github": "http://github.com/laracroft",
            "profileImage": "http://nodebbbb/api/authors/222/posts/217/image"
        },
        {
            // Second follower author object
        },
        {
            // Third follower author object
        }
        ]
    }
    '''
    author = get_object_or_404(Author, id=author_id)
    followers = Following.get_followers(author)
    followers_data = {
        "type": "followers",
        "followers": []
    }
    for follower in followers:
        follower_dataa = {
            "type": "author",
            "id": follower.author1.FQID,
            "host": follower.author1.host,
            "displayName": follower.author1.displayName,
            "page": follower.author1.page,
            "github": follower.author1.github,
            "profileImage": follower.author1.host+ follower.author1.profileImage.url
        }
        followers_data["followers"].append(follower_dataa)
    return Response(followers_data, status=200)

@api_view(['GET'])
def get_following(request, author_id):
    ''' example response
    {
    "type": "following",      
    "following":[
        {
            "type":"author",
            "id":"http://nodebbbb/api/authors/222",
            "host":"http://nodebbbb/api/",
            "displayName":"Lara Croft",
            "page":"http://nodebbbb/authors/222",
            "github": "
            "profileImage": "http://nodebbbb/api/authors/222/posts/217/image"
        },
        {
            // Second following author object
        },
        {
            // Third following author object
        }
        ]
    }
    '''
    author = get_object_or_404(Author, id=author_id)
    following = Following.get_following(author)
    following_data = {
        "type": "following",
        "following": []
    }
    for follow in following:
        following_dataa = {
            "type": "author",
            "id": follow.author2.FQID,
            "host": follow.author2.host,
            "displayName": follow.author2.displayName,
            "page": follow.author2.page,
            "github": follow.author2.github,
            "profileImage": follow.author2.host+follow.author2.profileImage.url
        }
        following_data["following"].append(following_dataa)
    return Response(following_data, status=200)


