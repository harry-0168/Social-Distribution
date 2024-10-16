from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
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
    return Response({})

@api_view(['POST'])
def signup(request):
    return Response({})

@api_view(['GET'])
def test_token(request):
    return Response({})

