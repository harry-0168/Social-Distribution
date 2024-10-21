from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404, reverse, get_object_or_404
from .models import Post, Comment, Like, Author
import base64
import jwt
import markdown
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from .serializers import PostSerializer
from author.views import get_author_from_cookie
from django.conf import settings
# Create your views here.
def post(request):
    author_id = get_author_from_cookie(request).data.get('id')
    author = get_object_or_404(Author, id=author_id)
    return render(request, "posts/createPost.html", {'author': author})
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

@api_view(['POST'])
def create_post(request):
    if request.method == 'POST':
        # Extract the author from the JWT token
        token = request.COOKIES.get('jwt')
        if not token:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            author = get_object_or_404(Author, display_name=payload['id'])
        except jwt.ExpiredSignatureError:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        except Author.DoesNotExist:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        # Extract post data from request
        title = request.POST['title']
        description = request.POST['description']
        content_type = request.POST['content_type']
        visibility = request.POST['visibility']
        content = request.POST.get('content', '')
        image = request.FILES.get('img')
        
        if content_type.startswith('image/') and image:
            # Read the image file and encode it as base64
            image_data = image.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            content = f"data:{image.content_type};base64,{encoded_image}"
        
        # Create a new post associated with the current author
        post = Post(
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
        # return Response(serializer.data, status=status.HTTP_201_CREATED)
        return redirect('home_page')

    return Response({"error": "Invalid request method"}, status=status.HTTP_400_BAD_REQUEST)

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
            author = get_object_or_404(Author, display_name=payload['id'])
        except jwt.ExpiredSignatureError:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        except Author.DoesNotExist:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

        # Use the existing post object to create a new post
        new_post = Post(
            title=f"{post.title}(Reposted: {post.author.display_name})",  # Add "Reposted:" to the title
            description=post.description,
            content_type=post.content_type,
            content=post.content,
            visibility=post.visibility,  # You can choose to change this if needed
            author=author,  # Use the author from the token
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
            author = get_object_or_404(Author, display_name=payload['id'])
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

    
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Ensure that only the author of the post or an admin can delete the post
    if post.author == request.user or request.user.is_superuser:
        post.visibility = 'DELETED'  # Mark the post as 'DELETED'
        post.save()
        return redirect('author_profile', author_id=post.author.id)  # Redirect to the author's profile page
    else:
        # If the user is not the author, they are redirected back
        return redirect('author_profile', author_id=post.author.id)
    
def edit_post(request, id):
    post = get_object_or_404(Post, id=id)
    author_id = get_author_from_cookie(request).data.get('id')
    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.description = request.POST.get('description')
        post.visibility = request.POST.get('visibility')
        post.content_type = request.POST.get('content_type')
        
        # Check if the content type is text
        if not request.POST.get('content_type').startswith('image/'):
            # Only update text content if the content type is not an image
            post.content = request.POST.get('content')
        
        # Check if a new image is uploaded
        image = request.FILES.get('img')
        if request.POST.get('content_type').startswith('image/') and image:
            # Read the image file and encode it as base64
            image_data = image.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            post.content = f"data:{image.content_type};base64,{encoded_image}"
        post.save()
        return redirect(reverse('author_profile', args=[post.author.id]))

    return render(request, 'posts/editPost.html', {'post': post, 'author_id': author_id})
    
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
    comments = post.comment_set.all()

    # Extract the author from the JWT token
    token = request.COOKIES.get('jwt')
    if not token and (post.visibility != 'PUBLIC' and post.visibility != 'UNLISTED'):
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    if token:
        try:
            # Decode the JWT token and get the author's display name
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            display_name = payload['id']  # Assuming 'id' holds the display_name or appropriate user identifier
        except jwt.ExpiredSignatureError:
            return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
        except Author.DoesNotExist:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        # Retrieve the form data
        username = display_name if token else "Anonymous"  # Assign anonymous for public/unlisted without JWT
        content = request.POST.get('content')

        # Create and save the new comment
        comment = Comment(username=username, content=content, post=post)
        comment.save()

        # Redirect to the same post after adding the comment (prevents form resubmission on refresh)
        return redirect('viewPost', id=post.id)

    return render(request, "posts/viewPost.html", {"id": id, "post": post, "author": author, "comments": comments})

def view_postLikes(request, id):
    post = get_object_or_404(Post, pk=id)

    if post.visibility == 'DELETED':    # TODO: add "and user is not admin"
        # Non-admin users should not see deleted posts
        return redirect('home_page')  # Redirect to index or a 404 page

    author = post.author

    return render(request, "posts/viewPostLikes.html", {"id":id, "post":post, "author":author})

def like_post(request, id):
    post = get_object_or_404(Post, pk=id)

    # Extract the author from the JWT token
    token = request.COOKIES.get('jwt')
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        # Decode the JWT token and get the author's display name
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        display_name = payload['id']  # Assuming 'id' is the display_name or can be replaced by actual key
    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        # Create and save the like, using the author's display name as the username
        like = Like(username=display_name, post=post)
        like.save()

    # Redirect back to the previous page using the HTTP_REFERER header
    previous_url = request.META.get('HTTP_REFERER', 'viewPost')  # 'view' is the fallback URL
    return redirect(previous_url)



def delete_post(request, id):
    post = get_object_or_404(Post, pk=id)

    # Mark post as "DELETED"
    post.visibility = 'DELETED'
    post.save()

    # Redirect to the index page or any other page
    return redirect('home_page')