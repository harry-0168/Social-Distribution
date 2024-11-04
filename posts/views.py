from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404, reverse, get_object_or_404
from .models import Post, Comment, Like, Author, githubPostIds, Following, Likes
import base64
import jwt
import markdown
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework import viewsets
from .serializers import PostSerializer, CommentSerializer, LikeSerializer
from author.views import get_author_from_cookie
from django.conf import settings
from django.contrib import messages
from urllib.parse import unquote
# Create your views here.
def post(request):
    author_id = get_author_from_cookie(request).data.get('id')
    author = get_object_or_404(Author, id=author_id)
    return render(request, "posts/createPost.html", {'author': author})

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

# CommentViewSet to manage Comment API actions
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

# LikeViewSet to manage Like API actions
class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer

# API to create a comment
@api_view(['POST'])
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    token = request.COOKIES.get('jwt')
    
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        username = payload['id']  # Assuming 'id' is the username or display name
        user = Author.objects.get(displayName=username)
    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    # Process the comment data
    content = request.data.get('content')
    if not content:
        return Response({"error": "Content is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    comment = Comment(username=username, content=content, post=post, author=user, type='comment')
    comment.save()
    
    # Serialize the created comment
    comment_serializer = CommentSerializer(comment)

    # Returning JSON for Ajax or redirect
    if request.accepts('application/json'):
        return Response(comment_serializer.data, status=status.HTTP_201_CREATED)
    else:
        return redirect('viewPost', id=post.id)

@api_view(['GET'])
def get_comment(request, FQID):
    print("in")
    print("FQID: ", FQID)
    # Decode the FQID to handle percent encoding
    decoded_FQID = unquote(FQID)
    
    # Retrieve the comment using the decoded FQID
    comment = get_object_or_404(Comment, FQID=decoded_FQID)
    print("comment: ", comment)
    # Prepare the data to be returned
    comment_data = {
        "id": comment.id,
        "type": comment.type,
        "contentType": comment.contentType,
        "username": comment.username,
        "published": comment.published,
        "content": comment.content,
        "post": comment.post.FQID,
        "FQID": comment.FQID,
        "author": {
            "id": comment.author.id,
            "host": comment.author.host,
            "displayName": comment.author.displayName,
            "github": comment.author.github,
            #"profile_image": comment.author.profile_image,
            "FQID": comment.author.FQID,  # Reference to the author's FQID
        }
    }
    
    # Return the comment data as a JSON response
    return Response(comment_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_posts_comments(request, author_id=None, post_id=None, FQID=None):
    if FQID:
        # Decode the FQID to find the post ID
        decoded_FQID = unquote(FQID)
        #post_id = decoded_FQID.split('/')[-1]  # Extract the post_id from the FQID
        post = get_object_or_404(Post, FQID=decoded_FQID)
    else:
        # Fetch the post using author_id and post_id
        post = get_object_or_404(Post, id=post_id)

    # Retrieve comments for the post
    comments = Comment.objects.filter(post=post)

    # Serialize the comments
    serializer = CommentSerializer(comments, many=True)

    # Return the comments
    return Response({"comments": serializer.data}, status=status.HTTP_200_OK)

class CommentPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'type': 'comments',
            'page_number': self.page.number,
            'size': self.page.paginator.per_page,
            'count': self.page.paginator.count,
            'src': data,
        })

@api_view(['GET', 'POST'])
def get_author_comments(request,  author_id=None, FQID=None):
    # Determine if the author is specified by UUID or FQID
    author = None
    if author_id:
        author = get_object_or_404(Author, id=author_id)
    elif FQID:
        author = get_object_or_404(Author, FQID=FQID)

    if request.method == 'GET':
        # Retrieve comments by the specified author
        comments = Comment.objects.filter(author=author)
        
        # Filter comments based on the visibility of the posts (for remote access)
        if request.user.is_anonymous:
            comments = comments.filter(post__visibility__in=["PUBLIC", "UNLISTED"])

        # Apply pagination
        paginator = CommentPagination()
        paginated_comments = paginator.paginate_queryset(comments, request)
        
        # Serialize the paginated data
        serializer = CommentSerializer(paginated_comments, many=True)
        
        # Return the paginated response
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        # Add a new comment for the specified author on a post
        data = request.data
        if data.get('type') != 'comment':
            return Response({'error': 'Invalid data type. Expected "comment".'}, status=status.HTTP_400_BAD_REQUEST)
        
        post_id = data.get('post')
        post = get_object_or_404(Post, id=post_id)
        
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save(author_id=author_id, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_commented_comment(request, author_id=None, comment_id=None, FQID=None):
    if author_id and comment_id:
        # Get the comment by author and comment UUIDs
        comment = get_object_or_404(Comment, id=comment_id, author__id=author_id)

    # Handle URL: /api/commented/{COMMENT_FQID}
    elif FQID:
        # Get the comment by its FQID
        comment = get_object_or_404(Comment, FQID=FQID)

    else:
        # If neither case matches, return a 400 error
        return Response({'error': 'Invalid parameters.'}, status=status.HTTP_400_BAD_REQUEST)

    # Serialize the comment and return the response
    serializer = CommentSerializer(comment)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    token = request.COOKIES.get('jwt')
    print("Request Data:", request.data)
    print("Request POST Data:", request.POST)  # Add this line to check what is in POST data

    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        username = payload['id']  # Assuming 'id' is the username or display name
        user = Author.objects.get(displayName=username)
    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    # Check if the user has already liked the post
    if Like.objects.filter(username=username, object=post).exists():
        #return Response({"error": "Post already liked"}, status=status.HTTP_400_BAD_REQUEST)
        #messages.error(request, "You have already liked this post.")
        return redirect(request.META.get('HTTP_REFERER'))

    like = Like(username=username, object=post, author=user)
    like.save()
    #messages.success(request, "Liked successfully!")
    like_serializer = LikeSerializer(like)
    # return Response(like_serializer.data, status=status.HTTP_201_CREATED)
    return redirect(request.META.get('HTTP_REFERER'))

@api_view(['POST'])
def api_create_like(request, author_id):
    # Debugging: Print the entire request data
    print("Request Data:", request.data)

    # Get the author based on the provided author_id
    author = get_object_or_404(Author, id=author_id)

    # Get the post_id from form data
    post_id = request.POST.get('post_id')  
    
    if not post_id:
        return Response({"error": "Post ID not found"}, status=status.HTTP_400_BAD_REQUEST)
    
    post = get_object_or_404(Post, id=post_id)
    token = request.COOKIES.get('jwt')

    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        username = payload['id']  # Assuming 'id' is the username or display name
        user = Author.objects.get(displayName=username)
    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    if Like.objects.filter(username=username, object=post).exists():
        return redirect(request.META.get('HTTP_REFERER'))

    # Create or get the Likes instance for the post
    likes_collection = Likes()
    post.likes_collection=likes_collection

    # Create a new Like instance
    like = Like(username=username, object=post, author=user)
    like.save()
    post.likes_collection.add_like(like)  # Ensure that add_like method is defined in Likes model

    like_serializer = LikeSerializer(like)
    return redirect(request.META.get('HTTP_REFERER'))

# Construct posts object for home page
class PostPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'type': 'posts',
            'page_number': self.page.number,
            'size': self.page.paginator.per_page,
            'count': self.page.paginator.count,
            'src': data,
        })

@api_view(['GET', 'POST'])
def get_posts_create_post(request, author_id):
    """Handles both fetching posts for home page and creating post"""

    if request.method == 'GET':
        author = get_object_or_404(Author, id=author_id)
        posts = Post.objects.all().order_by('-published')

        paginator = PostPagination()
        result_page = paginator.paginate_queryset(posts, request)

        # Filter posts based on visibility to the current user
        visible_posts = [post for post in result_page if post.is_visible_to(request.user)]
        serializer = PostSerializer(visible_posts, many=True)

        # Adjust the count to reflect only the visible posts
        paginated_response = paginator.get_paginated_response(serializer.data)
        paginated_response.data['count'] = len(visible_posts)

        return paginated_response

    elif request.method == 'POST':
        token = request.COOKIES.get('jwt')
        if not token:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            author = get_object_or_404(Author, displayName=payload['id'])
        except jwt.ExpiredSignatureError:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        except Author.DoesNotExist:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        # Extract post data from request
        title = request.POST.get('title')
        description = request.POST.get('description')
        content_type = request.POST.get('content_type')
        visibility = request.POST.get('visibility')
        content = request.POST.get('content', '')
        image = request.FILES.get('img')
        type = 'post'

        if content_type and content_type.startswith('image/') and image:
            # Read the image file and encode it as base64
            image_data = image.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            content = f"data:{image.content_type};base64,{encoded_image}"

        # Create a new post associated with the current author
        post = Post(
            type=type,
            title=title,
            description=description,
            content_type=content_type,
            content=content,
            visibility=visibility,
            author=author,  # Use the author from the token
        )
        post.save()

        # Serialize the post and return the response
        serializer = PostSerializer(post)
        return redirect('home_page')

@api_view(['POST'])
def repost_post(request, id):
    post = get_object_or_404(Post, pk=id)

    if request.method == 'POST':
        # Extract the author from the JWT token
        token = request.COOKIES.get('jwt')
        if not token:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            author = get_object_or_404(Author, displayName=payload['id'])
        except jwt.ExpiredSignatureError:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        except Author.DoesNotExist:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        # Use the existing post object to create a new post
        new_post = Post(
            title=f"{post.title}(Reposted: {post.author.displayName})",  # Add "Reposted:" to the title
            description=post.description,
            content_type=post.content_type,
            content=post.content,
            visibility=post.visibility,  # You can choose to change this if needed
            author=author,  # Use the author from the token
            type='repost'
        )
        
        new_post.save()

        # Serialize the new post and return the response
        serializer = PostSerializer(new_post)
        # return Response(serializer.data, status=status.HTTP_201_CREATED)
        return redirect('home_page')  # Redirect after successful repost

    return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def repost_link(request, id):
    post = get_object_or_404(Post, pk=id)

    if request.method == 'POST':
        # Extract the author from the JWT token
        token = request.COOKIES.get('jwt')
        if not token:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            author = get_object_or_404(Author, displayName=payload['id'])
        except jwt.ExpiredSignatureError:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        except Author.DoesNotExist:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        # Use the original post title and URL for the new repost
        # Get the current URL
        current_url = request.build_absolute_uri(request.path)
        
        # Remove the last part of the path
        base_url = '/'.join(current_url.split('/')[:-2])  # This removes the last two segments

    
        new_post = Post(
            title=f"Repost: {post.title}",  # Repost title
            description="",  # Optional description
            content_type="text/plain",  # Assuming you're using plain text for links
            #content=f"{request.build_absolute_uri(post.get_absolute_url())}",  # Set the content to the post link
            content = f"{base_url}",
            visibility=post.visibility,
            author=author,
        )
        
        new_post.save()

        # Serialize the new post and return the response
        serializer = PostSerializer(new_post)
        return redirect('home_page')  # Redirect after successful repost

    return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)

def view_edit_post(request, id):
    post = get_object_or_404(Post, id=id)
    author_id = get_author_from_cookie(request).data.get('id')
    return render(request, 'posts/editPost.html', {'post': post, 'author_id': author_id})

@api_view(['GET', 'POST'])
def get_edit_delete_post(request, author_id, post_id):
    post = get_object_or_404(Post, id=post_id)
    method = request.POST.get('_method', '').upper()
    try:
        # Make sure user who is not the author can't edit/delete the post
        if author_id != post.author.id and (method in ["PUT", "DELETE"] or request.method in ["PUT", "DELETE"]):
            return Response({"error": "Unauthorized to edit/delete other author's post"}, status=status.HTTP_403_FORBIDDEN)
    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
    if method == 'GET' or request.method == 'GET':
        if post.visibility == 'PUBLIC':
            serializer = PostSerializer(post)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Check for authentication and friendship for "friends-only" posts
        if post.visibility == 'FRIENDS':
            if request.user.is_authenticated and Following.are_friends(request.user, post.author):
                serializer = PostSerializer(post)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Unauthorized to view friends-only post"}, status=status.HTTP_403_FORBIDDEN)
    if method == 'PUT' or request.method == 'PUT':
        data = request.data.copy()  # Safely copy the data
        image = request.FILES.get('img')

        # Handle image upload
        if image:
            # Read and encode the image in base64
            image_data = image.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            # Set the encoded image as the content
            data['content'] = f"data:{image.content_type};base64,{encoded_image}"
        else:
            # Retain the original content if no new content is provided
            if not data.get('content'):
                data['content'] = post.content

        serializer = PostSerializer(post, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return redirect(reverse('author_profile', args=[author_id]))

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    if method == 'DELETE' or request.method == 'DELETE':
        # Ensure that only the author of the post or an admin can delete the post
        if post.author == request.user or request.user.is_superuser:
            post.visibility = 'DELETED'  # Mark the post as 'DELETED'
            post.save()

            post_serializer = PostSerializer(post)
            
            return redirect('author_profile', author_id=post.author.id)  # Redirect to the author's profile page
        else:
            # If the user is not the author, they are redirected back
            return redirect('author_profile', author_id=post.author.id)
    return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def get_post_image(request, author_id=None, post_id=None, FQID=None):
    # If author_id and post_id are provided, retrieve the post by post_id
    if author_id:
        # Retrieve the post using both author_id and post_id
        post = get_object_or_404(Post, id=post_id, author__id=author_id)
    elif FQID:
        post = get_object_or_404(Post, FQID=FQID)
    else:
        return Response({'error': 'Post ID or FQID must be provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if the content type is a base64 image
    if post.content_type in ['image/png;base64', 'image/jpeg;base64']:
        try:
            # Extract the base64 data after the comma
            encoded_data = post.content.split(',', 1)[1]
            print("encoded_DATA: ", encoded_data)
            # Decode the base64 content
            image_data = base64.b64decode(encoded_data)
            
            # Set the appropriate MIME type for the response
            mime_type = 'image/png' if 'png' in post.content_type else 'image/jpeg'
            
            # Return the binary image data in the response
            return HttpResponse(image_data, content_type=mime_type)
        
        except base64.binascii.Error:
            # Handle decoding error
            return Response({'error': 'Invalid base64 image data', 'content': post.content}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # If the content is not an image, return a 404 or error response
        return Response({'error': 'Image not found or content type is not an image', 'post.content_type': post.content_type}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_post_FQID(request, FQID=None):
    if FQID:
        post = get_object_or_404(Post, id=FQID)
        if post.visibility == 'PUBLIC':
            serializer = PostSerializer(post)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Check for authentication and friendship for "friends-only" posts
        if post.visibility == 'FRIENDS':
            if request.user.is_authenticated and Following.are_friends(request.user, post.author):
                serializer = PostSerializer(post)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Unauthorized to view friends-only post"}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({'error': 'FQID must be provided'}, status=status.HTTP_400_BAD_REQUEST)
    
def view_post(request, id):
    post = get_object_or_404(Post, pk=id)

    # Check for post visibility
    if post.visibility == 'DELETED' and not request.user.is_staff:  # Only admins can see deleted posts
        return redirect('home_page')  # Redirect non-admins to the home page

    if post.visibility == 'PRIVATE' and not request.user.is_authenticated:  # Private posts require authentication
        return redirect('login')  # Redirect unauthenticated users to login

    if post.visibility == 'UNLISTED' or post.visibility == 'PUBLIC':
        # Allow access for public and unlisted posts without authentication
        pass
    else:
        # For all other posts, ensure the user is authenticated
        if not request.user.is_authenticated:
            return redirect('login')

    author = post.author
    comments = post.comments.all()

    # Extract the author from the JWT token
    token = request.COOKIES.get('jwt')
    if not token and (post.visibility != 'PUBLIC' and post.visibility != 'UNLISTED'):
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    if token:
        try:
            # Decode the JWT token and get the author's display name
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            displayName = payload['id']  # Assuming 'id' holds the displayName or appropriate user identifier
        except jwt.ExpiredSignatureError:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
        except Author.DoesNotExist:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        # Retrieve the form data
        username = displayName if token else "Anonymous"  # Assign anonymous for public/unlisted without JWT
        content = request.POST.get('content')

        # Create and save the new comment
        comment = Comment(username=username, content=content, post=post)
        comment.save()

        # Redirect to the same post after adding the comment (prevents form resubmission on refresh)
        return redirect('viewPost', id=post.id)

    return render(request, "posts/viewPost.html", {"id": id, "post": post, "author": author, "comments": comments})

@api_view(['GET'])
def api_view_postLikes(request, author_id,post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.visibility == 'DELETED':    # TODO: add "and user is not admin"
        # Non-admin users should not see deleted posts
        return redirect('home_page')  # Redirect to index or a 404 page

    author = get_object_or_404(Author, id=author_id)

    return render(request, "posts/viewPostLikes.html", {"post_id": post_id, "post": post, "author": author})

@api_view(['GET'])
def api_view_Likes(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.visibility == 'DELETED':    # TODO: add "and user is not admin"
        # Non-admin users should not see deleted posts
        return redirect('home_page')  # Redirect to index or a 404 page

    author = post.author.id

    return render(request, "posts/viewPostLikes.html", {"post_id": post_id, "post": post, "author": author})

@api_view(['POST'])
def github_post(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    data = request.data
    check = githubPostIds.objects.filter(id=data['id'])
    if check:
        return Response({"error": "Post already exists"}, status=status.HTTP_200_OK)
    post = Post(
        title=data['title'],
        description=data['description'],
        content_type=data['content_type'],
        content=data['content'],
        visibility=data['visibility'],
        author=author
    )
    post.save()
    githubPost = githubPostIds(id=data['id'], post=post)
    githubPost.save()

    return Response(data, status=status.HTTP_200_OK)