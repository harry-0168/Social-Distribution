from django.shortcuts import render
from django.contrib.auth import get_user_model
from author.models import Author
import requests
import base64
from author.serializers import AuthorSerializer


User = get_user_model()

def search_results(request):
    query = request.GET.get('q', '')
    results = []
    # before we search, we need to fetch authors from other nodes and save them in our database, if they don't exist already
    # get all the node authors
    nodes = Author.objects.filter(isNode=True)
    print(nodes)
    for node in nodes:
        # make get request to the node's url with basic auth
        headers = {
                "Authorization": f"Basic {base64.b64encode(f'{node.displayName}:{node.first_name}'.encode()).decode()}",
                "Content-Type": "application/json"
                
            }
        print(node.host + 'authors', node.displayName, node.first_name)
        response = requests.get( url = node.host + '/api/authors', headers=headers)
        if response.status_code == 200:
            print(response.status_code)
            authors = response.json()['authors']
            for author in authors:
                # check if the author already exists in the database
                print(author)
                if not Author.objects.filter(id=author['id'], displayName = author['displayName']).exists():
                    # save the author in the database
                    author['password'] = 'password'  # set a dummy password
                    if author['host'].endswith('/api/'):
                        author['host'] = author['host'][:-5]
                        
                    serializer = AuthorSerializer(data=author)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        # do not do anything for now, skip
                        print(serializer.errors)
        else:
            print(response.status_code)

    if query:
        results = User.objects.filter(displayName__icontains=query)

    return render(request, 'search.html', {'results': results, 'query': query})
