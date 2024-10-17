from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from .models import Author  
from posts.models import Post  
from .serializers import AuthorSerializer
from django.shortcuts import render, get_object_or_404


def profile_view(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    posts = Post.objects.filter(author=author).order_by('-published')
    return render(request, 'author/author_feed.html', {'author': author, 'posts': posts})

def author_about(request, author_id):
    author = Author.objects.get(id=author_id)  
    return render(request, 'author/author_about.html', {'author': author})

class AuthorPagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'size'  
    max_page_size = 500  

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = AuthorPagination

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

##########
''' Code for Author authentication/ Login to our website '''
@api_view(['POST'])
def login(request):
    author = get_object_or_404(Author, display_name = request.data['display_name'])
    if not author.check_password(request.data['password']):
        return Response({"detail":"Not found"}, status= status.HTTP_404_NOT_FOUND)
    token, created = Token.objects.get_or_create(user = author)
    serializer = AuthorSerializer(instance = author)
    return Response({"token":token.key,"author":serializer.data})

@api_view(['POST'])
def signup(request):
    serializer = AuthorSerializer(data = request.data, partial= True)
    if serializer.is_valid():
        serializer.save()
        author = Author.objects.get(display_name=request.data['display_name'])
        author.set_password(request.data['password'])
        author.save()
        token = Token.objects.create(user = author)
        return Response({"token":token.key,"author":serializer.data})

    return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)

from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes(IsAuthenticated)
def test_token(request):
    ''' This function is to verify if forbidden routes work with the auth token'''

    return Response(request.user)

