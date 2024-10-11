from django.shortcuts import render, redirect
from .models import Post

# Create your views here.
def index(request):
    return render(request, "posts/createPost.html")

def create_post(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        visibility = request.POST['visibility']
        post = Post(
            title=title,
            description=description,
            content_type='text/plain',
            content=description,
            visibility=visibility,
            # author=request.user.author,
        )
        post.save() 
        #TO-DO change redirection
        return redirect('index')