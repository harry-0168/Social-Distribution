from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.response import Response
from rest_framework import status
import jwt
from django.conf import settings
from .models import Notification
from rest_framework.decorators import api_view, action,authentication_classes, permission_classes
from author.models import Author, FollowRequest
from django.contrib.contenttypes.models import ContentType
from posts.models import Post, Comment, Like, Likes
from posts.serializers import PostSerializer
from django.conf import settings
import json
from author.models import Following
from .models import Inbox
from django.utils import timezone
import logging
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated

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
        comments = Comment.objects.filter(author=author)
        comment_notifications = Comment.objects.filter(post__in=posts)
        like_notifications = Like.objects.filter(post__in=posts) | Like.objects.filter(comment__in=comments)

        
        # Get the list of authors that the current user is following
        followed_authors = Following.objects.filter(author1=author).values_list('author2', flat=True)
        # Filter for repost notifications where the author is in the list of followed authors
        repost_notifications = Post.objects.filter(author__in=followed_authors, type="repost")

        # Serialize the querysets to JSON-serializable data
        
        follow_requests_data = list(follow_req_notifications.values('id', 'author1__id', 'author2__id', 'author1__displayName','author1__profileImage','date'))
        comment_data = list(comment_notifications.values('id', 'username', 'comment', 'published', 'post__title', 'author__profileImage', 'author__displayName'))
        like_data = list(
            like_notifications.values(
                'uuid',
                'username',
                'post__title',       # For likes on posts
                'comment__comment',  # For likes on comments (assuming 'content' is the field for comment text)
                'published',
                'author__displayName',
                'author__profileImage'
            )
        )
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
@authentication_classes([BasicAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def inboxApi(request, object_author_serial):
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
                print(parsed_data['actor']['id'], author.id)
                if author.id != parsed_data['actor']['id']:
                    return Response({"error": "Invalid request"}, status=401)
                # if parsed_data['object']['host'] != parsed_data['actor']['host']:
                #     # create object author and following object, then forward the request to the next host server
                #     AuthorSerializer = AuthorSerializer(id=parsed_data['object']['id'], host=parsed_data['object']['host'], displayName=parsed_data['object']['displayName'], github=parsed_data['object']['github'], profileImage=parsed_data['object']['profileImage'], page=parsed_data['object']['url'])
                #     if AuthorSerializer.is_valid():
                #         AuthorSerializer.save()
                #     else:
                #         return Response({"error": "Invalid object author data"}, status=400)
                #     object_author = Author.objects.get(id=parsed_data['object']['id'])
                #     if not Following.follow(actor, object_author):
                #         return Response({"error": "Already following"}, status=400)
                #     return Response({"error": "Forwarding request to the next host server"}, status=200)
                actor = get_object_or_404(Author, id=parsed_data['actor']['id'])
                object_author = get_object_or_404(Author, id=parsed_data['object']['id'])
                # check if the actor is already following the object_author
                if actor.id == object_author.id:
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
            object_author = Author.objects.get(author_serial=parsed_data['object']['post']['author'])
            Inbox(receiver=object_author, type='comment', FQIDorId=parsed_data['object']['id'], received_at=timezone.now()).save()
            return Response({"message": "Comment sent"}, status=200)
        
        elif parsed_data['type'] == 'like':
            author = get_object_or_404(Author, author_serial=object_author_serial)

            # Get the post_id from form data
            post_id = request.POST.get('post_id')
            comment_id = request.POST.get('comment_id')

            token = request.COOKIES.get('jwt')
            if not token:
                return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                username = payload['id']  # Assuming 'id' is the username or display name
                user = get_object_or_404(Author, displayName=username)
            except jwt.ExpiredSignatureError:
                return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                if post_id:
                    post = get_object_or_404(Post, uuid=post_id)
                    print("level1")
                    

            

                    # Check if a like already exists
                    if Like.objects.filter(username=username, post=post).exists():
                        print("level2")
                        likes = Like.objects.filter(username=username, post=post)
                        for like in likes:
                            print(f"Like ID: {like.uuid}, Username: {like.username}, Author: {like.author}, Post ID: {like.post.id}")
                        return redirect(request.META.get('HTTP_REFERER'))

                    try:
                        # Ensure post has a likes collection or create one
                        if not post.likes_collection:
                            likes_collection = Likes.objects.create()
                            post.likes_collection = likes_collection
                            post.save()

                        # Create and save the new Like instance
                        like = Like(username=username, post=post, author=user)
                        like.save()

                        # Add the like to the post's likes collection
                        post.likes_collection.add_like(like)
                        #Inbox(receiver=author, type='like', FQIDorId=parsed_data['object']['id'], received_at=timezone.now()).save()
                        print("level3")

                        # Serialize and return the response
                        return redirect(request.META.get('HTTP_REFERER'))
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


                    """
                    print("Reached post logic")
                    post = get_object_or_404(Post, uuid=post_id)
                    # Check if a like already exists for the post
                    existing_likes = Like.objects.filter(username=username, post=post)
                    print(f"Existing likes count: {existing_likes.count()}")
                    if existing_likes.exists():
                        print("Like already exists.")
                        return redirect(request.META.get('HTTP_REFERER'))

                    # Ensure post has a likes collection or create one
                    if not post.likes_collection:
                        likes_collection = Likes.objects.create()
                        post.likes_collection = likes_collection
                        post.save()

                    # Create and save the new Like instance for the post
                    like = Like(username=username, post=post, author=user)
                    like.save()

                    # Add the like to the post's likes collection
                    post.likes_collection.add_like(like)
                    print("Like created successfully for post")
                    return redirect(request.META.get('HTTP_REFERER'))"""

                elif comment_id:
                    comment = get_object_or_404(Comment, id=comment_id)
                    print("level1")
                    

            

                    # Check if a like already exists
                    if Like.objects.filter(username=username, comment=comment).exists():
                        print("level2")
                        likes = Like.objects.filter(username=username, comment=comment)
                        for like in likes:
                            print(f"Like ID: {like.uuid}, Username: {like.username}, Author: {like.author}, Comment ID: {like.comment.id}")
                        likes_collections = Likes.objects.all()
                        print("All Likes Collections:")
                        for collection in likes_collections:
                            print(f"Likes Collection ID: {collection.id}")
                            print(f"Page: {collection.page}")
                            print(f"Page Number: {collection.page_number}")
                            print(f"Size: {collection.size}")
                            print(f"Total Likes: {collection.count}")
                            
                            # Print all likes in the collection (related Like objects)
                            print("Likes in this collection:")
                            for like in collection.src.all():
                                print(f"  - {like.username} liked {'post' if like.post else 'comment'} ID {like.post.id if like.post else like.comment.id}")
                            
                            print("-" * 50)
                        return redirect(request.META.get('HTTP_REFERER'))
                            

                    try:
                        # Ensure post has a likes collection or create one
                        if not comment.likes_collection:
                            likes_collection = Likes.objects.create()
                            comment.likes_collection = likes_collection
                            comment.save()

                        # Create and save the new Like instance
                        like = Like(username=username, comment=comment, author=user)
                        like.save()

                        # Add the like to the post's likes collection
                        comment.likes_collection.add_like(like)
                        print("level3")
                        print(parsed_data)
                        #Inbox(receiver=author, type='like', FQIDorId=parsed_data['object']['id'], received_at=timezone.now()).save()


                        # Serialize and return the response
                        return redirect(request.META.get('HTTP_REFERER'))
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    """

                    print("Reached comment logic")
                    comment = get_object_or_404(Comment, id=comment_id)
                    # Check if a like already exists for the comment
                    existing_likes = Like.objects.filter(username=username, comment=comment)
                    print(f"Existing likes count for comment: {existing_likes.count()}")
                    if existing_likes.exists():
                        print("Like already exists for comment.")
                        return redirect(request.META.get('HTTP_REFERER'))

                    # Ensure comment has a likes collection or create one
                    if not comment.likes_collection:
                        likes_collection = Likes.objects.create()
                        comment.likes_collection = likes_collection
                        comment.save()

                    # Create and save the new Like instance for the comment
                    like = Like(username=username, comment=comment, author=user)
                    like.save()

                    # Add the like to the comment's likes collection
                    comment.likes_collection.add_like(like)
                    print("Like created successfully for comment")
                    return redirect(request.META.get('HTTP_REFERER'))"""

                else:
                    return Response({"error": "Post ID or Comment ID not found"}, status=status.HTTP_400_BAD_REQUEST)


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
    
@api_view(['GET', 'DELETE', 'PUT'])
@authentication_classes([BasicAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def handle_follow_request_response(request, author_serial, foreign_author_fqid):
    token = request.COOKIES.get('jwt')
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        author = get_object_or_404(Author, displayName=payload['id']) # author that sent the request
        if author.author_serial != author_serial:
            return Response({"error": "Unauthorized"}, status=401)
        
        # foreign_author_fqid will be percent encoded, so we need to decode it
        from urllib.parse import unquote
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


