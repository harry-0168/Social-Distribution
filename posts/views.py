from django.shortcuts import get_object_or_404, redirect
from .models import Post
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