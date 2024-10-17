from django.shortcuts import render, redirect, get_object_or_404, reverse, get_object_or_404
from .models import Post, Comment, Like, Author
import base64

# Create your views here.
def post(request):
    return render(request, "posts/createPost.html")

def create_post(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        contentType = request.POST['content_type']
        visibility = request.POST['visibility']
        content = request.POST.get('content', '')
        image = request.FILES.get('img')
        author = get_object_or_404(Author, id=1)
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
            author=author,
        )
        post.save() 
        return redirect('home_page')
    
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
    
def edit_post(request):
    post = get_object_or_404(Post, id='dd8e3def6fd54d79ab860bea621bb9a6')

    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.description = request.POST.get('description')
        post.visibility = request.POST.get('visibility')
        post.content_type = request.POST.get('content_type')
        post.content = request.POST.get('content')
        post.save()
        return redirect('edit_post')

    return render(request, 'posts/editPost.html', {'post': post})

    return redirect('index')
    
def view_post(request, id):
    post = get_object_or_404(Post, pk=id)
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
    
    # Redirect back to the same post page using 'reverse'
    return redirect('likes', id=post.id)