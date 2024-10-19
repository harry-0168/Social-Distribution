from django.shortcuts import render, redirect, get_object_or_404, reverse, get_object_or_404
from .models import Post, Comment, Like, Author
import base64
import markdown

# Create your views here.
def post(request):
    return render(request, "posts/createPost.html")

def create_post(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        content_type = request.POST['content_type']
        visibility = request.POST['visibility']
        content = request.POST.get('content', '')
        image = request.FILES.get('img')
        author = get_object_or_404(Author, id='67d4c836-99a1-4460-87b7-03d2b2375a07')
        if content_type.startswith('image/') and image:
            # Read the image file and encode it as base64
            image_data = image.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            content = f"data:{image.content_type};base64,{encoded_image}"
        
        post = Post(
            title=title,
            description=description,
            content_type=content_type,
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
    
def edit_post(request, id):
    post = get_object_or_404(Post, id=id)

    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.description = request.POST.get('description')
        post.visibility = request.POST.get('visibility')
        post.content_type = request.POST.get('content_type')
        post.content = request.POST.get('content')
        post.save()
        return redirect('edit_post')

    return render(request, 'posts/editPost.html', {'post': post})
    
def view_post(request, id):
    post = get_object_or_404(Post, pk=id)

    if post.visibility == 'DELETED':    # TODO: add "and user is not admin"
        # Non-admin users should not see deleted posts
        return redirect('index')  # Redirect to index or a 404 page

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
        return redirect('index')  # Redirect to index or a 404 page

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
    return redirect('index')