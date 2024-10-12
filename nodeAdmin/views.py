from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
import requests
from author.models import Author
from django.conf import settings
import json



def manage_dashboard(request):
    return render(request, "nodeAdmin/admin_dashboard.html")

def manage_notifications(request):
    return render(request, "nodeAdmin/admin_notifications.html")

def manage_authors(request):
    authors = Author.objects.all()
    current_host = request.get_host()
    return render(
        request, 'nodeAdmin/admin_authors.html',{'authors': authors, 'current_host': current_host})

def api_list_authors(request):
    if request.method == 'GET':
        authors = Author.objects.all()
        data = {"type": "authors", "authors": list(authors.values())}  # Convert QuerySet to list of dictionaries
        return JsonResponse(data)

def api_add_author(request):
    if request.method == 'POST':
        try:

            author_data = {
                'display_name': request.POST.get('display_name'),
                'host': f"http://{request.get_host()}",  # set host 
                'github': request.POST.get('github'),
                'profile_image': request.POST.get('profile_image'),
                'page': request.POST.get('page')
            }

            Author.objects.create(**author_data)

            return JsonResponse({"message": "Author created successfully"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)






def api_author_detail(request, author_id):
    # GET request to retrieve a single author
    if request.method == 'GET':
        author = get_object_or_404(Author, id=author_id)
        data = {
            "type": "author",
            "id": author.id,
            "host": author.host,
            "display_name": author.display_name,
            "github": author.github,
            "profile_image": author.profile_image,
            "page": author.page,
        }
        return JsonResponse(data)
    
    # PUT request to modify an author
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)

            author = get_object_or_404(Author, id=author_id)

            author.display_name = data.get('display_name', author.display_name)
            author.github = data.get('github', author.github)
            author.profile_image = data.get('profile_image', author.profile_image)
            author.page = data.get('page', author.page)

            author.save()

            return JsonResponse({'message': 'Author modified successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return HttpResponseNotFound()
    

# Delete an author
def api_delete_author(request, author_id):
    if request.method == 'DELETE':
        author = get_object_or_404(Author, id=author_id)
        author.delete()
        return JsonResponse({'message': 'Author deleted successfully'}, status=204)
    return HttpResponseNotFound()
    

def manage_posts(request):
    return render(request, "nodeAdmin/admin_posts.html")

def manage_nodes(request):
    return render(request, "nodeAdmin/admin_nodes.html")

def manage_settings(request):
    return render(request, "nodeAdmin/admin_settings.html")