from django.shortcuts import render, redirect, get_object_or_404
from .models import Post
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
    page = get_object_or_404(Post, pk=id)
    published = page.published
    title = page.title
    description = page.description
    return render(request, "posts/viewPost.html", {"id":id, "published":published, "title":title, "description":description})