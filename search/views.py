from django.shortcuts import render
from django.contrib.auth import get_user_model

User = get_user_model()

def search_results(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        results = User.objects.filter(display_name__icontains=query)

    return render(request, 'search.html', {'results': results, 'query': query})
