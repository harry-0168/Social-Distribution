from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.response import Response
from rest_framework import status
import jwt
from django.conf import settings
from .models import Notification
from rest_framework.decorators import api_view, action,authentication_classes, permission_classes
from author.models import Author, FollowRequest
from posts.models import Post, Comment, Like, Likes
from posts.serializers import PostSerializer
from django.conf import settings
import json
from author.models import Following
from .models import Inbox
from django.utils import timezone
import logging
from urllib.parse import unquote
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from author.serializers import AuthorSerializer
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
import requests
import base64
from django.views.decorators.csrf import csrf_exempt

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
        like_notifications = Like.objects.filter(object__in=posts)
        
        # Get the list of authors that the current user is following
        followed_authors = Following.objects.filter(author1=author).values_list('author2', flat=True)
        # Filter for repost notifications where the author is in the list of followed authors
        repost_notifications = Post.objects.filter(author__in=followed_authors, type="repost")

        # Serialize the querysets to JSON-serializable data
        
        follow_requests_data = list(follow_req_notifications.values('id', 'author1__id', 'author2__id', 'author1__displayName','author1__profileImage','date'))
        comment_data = list(comment_notifications.values('id', 'username', 'comment', 'published', 'post__title', 'author__profileImage', 'author__displayName'))
        like_data = list(like_notifications.values('id', 'username', 'object__title', 'published', 'author__displayName', 'author__profileImage'))
        repost_data = list(repost_notifications.values('id', 'author__displayName', 'content', 'title', 'author__profileImage'))

        # Send the data to the template
        for follow_request in follow_requests_data:
            follow_request['author1__profileImage'] = author.host + settings.MEDIA_URL +follow_request['author1__profileImage']
            author_id = follow_request['author1__id']
            author = get_object_or_404(Author, id=author_id)
            follow_request['profileImage'] = author.profileImage        
        for comment in comment_data:
            comment['author__profileImage'] = author.host + settings.MEDIA_URL + comment['author__profileImage']
            username = comment['username']
            author = get_object_or_404(Author, displayName=username)
            comment['profileImage'] = author.profileImage 
        for like in like_data:
            like['author__profileImage'] = author.host + settings.MEDIA_URL + like['author__profileImage']
            username = like['username']
            author = get_object_or_404(Author, displayName=username)
            like['profileImage'] = author.profileImage 
        for repost in repost_data:
            repost['author__profileImage'] = author.host + settings.MEDIA_URL + repost['author__profileImage']
            username = repost['author__displayName']
            author = get_object_or_404(Author, displayName=username)
            repost['profileImage'] = author.profileImage 
        
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
@csrf_exempt
def inboxApi(request, object_author_serial):
    token = request.COOKIES.get('jwt')
    flag = 1   # flag to check if the request is from my nodes frontend
    payload, author, actor, object_author = None, None, None, None
    if not token:
        flag = 0
        auth = BasicAuthentication()
        user, auth_status = auth.authenticate(request)
        if  not user or not IsAuthenticated().has_permission(request, None):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        if flag == 1:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            author = get_object_or_404(Author, displayName=payload['id']) # author that sent the request

        # Parse JSON string into a Python dictionary
        parsed_data = request.data

        # check the type of request object
        if parsed_data['type'] == 'follow':
            try:
                if parsed_data['object']['host'] != parsed_data['actor']['host']:
                    
                    # create object author and following object, then forward the request to the next host server
                    objectAuthor = Author.objects.get(id=parsed_data['object']['id'])
                    print(parsed_data['actor']['id'])
                    # actor_data = {
                    #     "FQID": parsed_data['actor']['id'],
                    #     "host": parsed_data['actor']['host'],
                    #     "displayName": parsed_data['actor']['displayName'],
                    #     "github": parsed_data['actor']['github'],
                    #     "profileImage": parsed_data['actor']['profileImage'],
                    #     "page": parsed_data['actor']['page'],
                    # }
                    actorSerializer = AuthorSerializer(data=parsed_data["actor"], partial=True)

                    if actorSerializer.is_valid():
                        actorSerializer.save()
                    # else:
                    #     return Response({"error": "Invalid object author data","serializer":actorSerializer.errors}, status=400)
                    actor = Author.objects.get(id=parsed_data['actor']['id'])
                    if not actor:
                        return Response({"error": "Actor not found"}, status=404)
                else:
                    actor = get_object_or_404(Author, id=parsed_data['actor']['id'])
                    objectAuthor = get_object_or_404(Author, id=parsed_data['object']['id'])
                    # check if the actor is already following the object_author
                    if actor.id == objectAuthor.id:
                        return Response({"error": "Cannot follow yourself"}, status=400)
                new = Following.follow(actor, objectAuthor)
                if not new:
                    return Response({"error": "Already following"}, status=400)
                
                inboxxx = Inbox(receiver=objectAuthor, type='follow', FQIDorId=new.id, received_at=timezone.now()).save()

                return Response({"message": "Follow request sent","requestStatus":new.status}, status=200)


            
            except Author.DoesNotExist:
                # forward the request to the next host server if host is not the current host
                # if actor does not exist create it and send a follow request to the object_author
                # if object_author does not exist forward the request to the next host server inbox
                return Response({"error": "Actor not found"}, status=404)
            
        elif parsed_data['type'] == 'comment':
            object_author = Author.objects.get(author_serial=parsed_data['object']['post']['author'])
            Inbox(receiver=object_author, type='comment', FQIDorId=parsed_data['object']['id'], received_at=timezone.now()).save()
            return Response({"message": "Comment sent"}, status=200)
        
        elif parsed_data['type'] == 'like':
            author = get_object_or_404(Author, author_serial=object_author_serial)

            # Get the post_id from form data
            post_id = request.POST.get('post_id')
            if not post_id:
                return Response({"error": "Post ID not found"}, status=status.HTTP_400_BAD_REQUEST)
            
            post = get_object_or_404(Post, uuid=post_id)

            token = request.COOKIES.get('jwt')
            if not token:
                return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                username = payload['id']  # Assuming 'id' is the username or display name
                user = get_object_or_404(Author, displayName=username)
            except jwt.ExpiredSignatureError:
                return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

            # Check if a like already exists
            if Like.objects.filter(username=username, object=post).exists():
                return redirect(request.META.get('HTTP_REFERER'))

            try:
                # Ensure post has a likes collection or create one
                if not post.likes_collection:
                    likes_collection = Likes.objects.create()
                    post.likes_collection = likes_collection
                    post.save()

                # Create and save the new Like instance
                like = Like(username=username, object=post, author=user)
                like.save()

                # Add the like to the post's likes collection
                post.likes_collection.add_like(like)

                # Serialize and return the response
                return redirect(request.META.get('HTTP_REFERER'))

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif parsed_data['type'] == 'post':
            serializer = PostSerializer(data=parsed_data)
            if serializer.is_valid():
                # Check if post exists and update it if needed
                post, created = Post.objects.update_or_create(
                    id=parsed_data.get('id'),
                    defaults={
                        'type': 'post',
                        'title': parsed_data.get('title'),
                        'description': parsed_data.get('description'),
                        'contentType': parsed_data.get('contentType'),
                        'content': parsed_data.get('content'),
                        'visibility': parsed_data.get('visibility'),
                        'author': author,
                        'page': parsed_data.get('page')
                    }
                )
                return Response({"message": "Post received"}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=401)
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid token"}, status=401)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=404)
    # except Exception as e:
    #     return Response({"error": str(e)}, status=400)
    
@api_view(['GET', 'DELETE', 'PUT'])
def handle_follow_request_response(request, author_serial, foreign_author_fqid):
    token = request.COOKIES.get('jwt')
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        author = get_object_or_404(Author, displayName=payload['id']) # author that sent the request

        
        # foreign_author_fqid will be percent encoded, so we need to decode it
        
        foreign_author_fqid = unquote(foreign_author_fqid).rstrip('/')
        print(f"Decoded foreign_author_fqid: {foreign_author_fqid}")
        foreign_author = get_object_or_404(Author, id=foreign_author_fqid)
        if request.method == 'PUT':
            # Accept follow request from foreign_author 
            follow_request = get_object_or_404(Following, author1 = foreign_author, author2 = author, status='pending')
            follow_request.status = 'accepted'
            follow_request.save()
            return Response({"message": "Follow request accepted"}, status=200)
        elif request.method == 'DELETE':
            # Reject follow request from foreign_authorm, status can be 'pending' or 'accepted'
            follow_request = get_object_or_404(Following, author1 = author, author2 = foreign_author)
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

@api_view(['POST'])
def forward_follow_request(request):
    ''' This view is used to forward follow requests to the next host server if the object author is not on the current host server '''
    request_data = request.data
    # check if the object author is on the current host server
    object_author = get_object_or_404(Author, id=request_data['object']['id'])
    actor = get_object_or_404(Author, id=request_data['actor']['id'])
    if object_author.host == request.get_host():
        return Response({"error": "Object author is on the current host server"}, status=400)
    else:
        # find author with the same host as object_author and isNode=True
        print(object_author.host, object_author.displayName)
        node_author = Author.objects.filter(host=object_author.host, isNode=True).first()
        if not node_author:
            return Response({"error": "Node author not found"}, status=404)
        # forward the follow request to the object_author's host
        payload = {
            "type": "follow",
            "summary": f"{actor.displayName} wants to follow {object_author.displayName}",
            "actor": {
                "type": "author",
                "id": actor.id,
                "host": actor.host,
                "displayName": actor.displayName,
                "github": actor.github,
                "profileImage": actor.host + actor.profileImage,
                "page": actor.page
            },
            "object": {
                "type": "author",
                "id": object_author.id,
                "host": object_author.host,
                "displayName": object_author.displayName,
                "page": object_author.page,
                "github": object_author.github,
                "profileImage": object_author.profileImage
            }
        }
        print(node_author.displayName, node_author.first_name, object_author.id+'/inbox')
        # using http basic auth to authenticate with the node server using the node_author's username and password
        headers = {
                "Authorization": f"Basic {base64.b64encode(f'{node_author.displayName}:{node_author.first_name}'.encode()).decode()}",
                "Content-Type": "application/json",
                "host": node_author.host.split('//')[1],
            }
        print(headers)
        new = Following.follow(actor, object_author)
        if not new:
            return Response({"error": "Already following"}, status=400)
        follow = Following.objects.get(author1=actor, author2=object_author)
        follow.status = 'accepted'
        follow.save()
        

        response = requests.post(object_author.id + '/inbox', json=payload, headers=headers)
        print(response.status_code, response.text)

        return Response({"message": "Follow request forwarded"}, status=200)


@api_view(['GET'])
@authentication_classes([BasicAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_followers(request, author_serial):
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
    author = get_object_or_404(Author, author_serial=author_serial)
    followers = Following.get_followers(author)
    followers_data = {
        "type": "followers",
        "followers": []
    }
    for follower in followers:
        follower_dataa = {
            "type": "author",
            "id": follower.author1.id,
            "host": follower.author1.host,
            "displayName": follower.author1.displayName,
            "page": follower.author1.page,
            "github": follower.author1.github,
            "profileImage": follower.author1.host+ follower.author1.profileImage.url
        }
        followers_data["followers"].append(follower_dataa)
    return Response(followers_data, status=200)

@api_view(['GET'])
@authentication_classes([BasicAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_following(request, author_serial):
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
    author = get_object_or_404(Author, author_serial=author_serial)
    following = Following.get_following(author)
    following_data = {
        "type": "following",
        "following": []
    }
    for follow in following:
        following_dataa = {
            "type": "author",
            "id": follow.author2.id,
            "host": follow.author2.host,
            "displayName": follow.author2.displayName,
            "page": follow.author2.page,
            "github": follow.author2.github,
            "profileImage": follow.author2.host+follow.author2.profileImage.url
        }
        following_data["following"].append(following_dataa)
    return Response(following_data, status=200)


