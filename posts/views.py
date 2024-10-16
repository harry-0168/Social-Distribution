from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, Author
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
        #TO-DO change redirection
        return redirect('index')
    
def edit_post(request):
    post = get_object_or_404(Post, id='dd8e3def6fd54d79ab860bea621bb9a6')

    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.description = request.POST.get('description')
        post.visibility = request.POST.get('visibility')
        post.content_type = request.POST.get('content_type')
        post.content = request.POST.get('content')
        post.save()
        return redirect('post_list')  # Redirect to post list or detail page

    return render(request, 'posts/editPost.html', {'post': post})