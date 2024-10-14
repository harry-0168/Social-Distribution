from django.shortcuts import render, redirect,get_object_or_404
from .models import Post
import base64
import markdown

# Create your views here.
def index(request):
    return render(request, "posts/createPost.html")

def create_post(request):
    if request.method == 'POST':
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
        
        post = Post(
            title=title,
            description=description,
            content_type=content_type,
            content=content,
            visibility=visibility,
            # author=request.user.author,
        )
        post.save()
        #TO-DO change redirection
        return redirect('view_post', post_id = post.id)
    return render(request, 'posts/createPost.html') #If request method not POST, redirect to the createPost page


def view_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_image = post.content_type.startswith('image/')
    if post.content_type == 'text/markdown':
        post.content = markdown.markdown(post.content)
    
    return render(request, 'posts/viewPost.html', {'post': post, 'is_image': is_image})