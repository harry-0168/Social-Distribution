from django.shortcuts import render
from author.models import Author

# Create your views here.
def manage_dashboard(request):
    return render(request, "nodeAdmin/admin_dashboard.html")

def manage_notifications(request):
    return render(request, "nodeAdmin/admin_notifications.html")

def manage_authors(request):
    # Fetch all authors from the database
    authors = Author.objects.all()
    # Render the template with the list of authors
    return render(request, 'nodeAdmin/admin_authors.html', {'authors': authors})

def manage_posts(request):
    return render(request, "nodeAdmin/admin_posts.html")

def manage_nodes(request):
    return render(request, "nodeAdmin/admin_nodes.html")

def manage_settings(request):
    return render(request, "nodeAdmin/admin_settings.html")