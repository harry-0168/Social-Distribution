from django.shortcuts import render, redirect, get_object_or_404, reverse
from .models import Post, Comment, Like
import base64

# Create your views here.
def index(request):
    return render(request, "posts/createPost.html")

def create_post(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        contentType = request.POST['content_type']
        visibility = request.POST['visibility']
        content = request.POST.get('content', '')
        image = request.FILES.get('img')

        if contentType.startswith('image/') and image:
            # Read the image file and encode it as base64
            image_data = image.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            content = f"data:{image.content_type};base64,{encoded_image}"
        post = Post(
            title=title,
            description=description,
            content_type=contentType,
            content=content,
            visibility=visibility,
            # author=request.user.author,
        )
        post.save() 
        #TO-DO change redirection
    return redirect('index')
    
def view_post(request, id):
    post = get_object_or_404(Post, pk=id)

    if post.visibility == 'DELETED':    # TODO: add "and user is not admin"
        # Non-admin users should not see deleted posts
        return redirect('home_page')  # Redirect to index or a 404 page

    published = post.published
    title = post.title
    description = post.description

    if request.method == 'POST':
        # Retrieve the form data
        username = request.POST['username']
        content = request.POST['content']
        
        # Create and save the new comment
        comment = Comment(username=username, content=content, post=post)
        comment.save()
        
        # Redirect to the same post after adding the comment (prevents form resubmission on refresh)
        return redirect('view', id=post.id)

    return render(request, "posts/viewPost.html", {"id":id, "published":published, "title":title, "description":description, "post":post})

def view_postLikes(request, id):
    post = get_object_or_404(Post, pk=id)

    if post.visibility == 'DELETED':    # TODO: add "and user is not admin"
        # Non-admin users should not see deleted posts
        return redirect('home_page')  # Redirect to index or a 404 page

    published = post.published
    title = post.title
    description = post.description

    return render(request, "posts/viewPostLikes.html", {"id":id, "published":published, "title":title, "description":description, "post":post})

def like_post(request, id):
    post = get_object_or_404(Post, pk=id)
    
    if request.method == 'POST':
        # Create and save the like
        like = Like(post=post)
        like.save()
    
    # Redirect back to the previous page using the HTTP_REFERER header
    previous_url = request.META.get('HTTP_REFERER', 'view')  # 'view' is the fallback URL
    return redirect(previous_url)

def delete_post(request, id):
    post = get_object_or_404(Post, pk=id)

    # Mark post as "DELETED"
    post.visibility = 'DELETED'
    post.save()

    # Redirect to the index page or any other page
    return redirect('home_page')