from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from .models import Author  
from posts.models import Post  
from .serializers import AuthorSerializer
from django.shortcuts import render, get_object_or_404
import jwt
from datetime import datetime, timedelta
from rest_framework.exceptions import AuthenticationFailed  


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
    if not author.isVerified:
        return Response({"detail":"Not Verified by admin"}, status= status.HTTP_401_UNAUTHORIZED)
    if not author.check_password(request.data['password']):
        return Response({"detail":"Not found"}, status= status.HTTP_404_NOT_FOUND)
    # token, created = Token.objects.get_or_create(user = author)
    payload = {
        'id': author.display_name,
        'exp': datetime.now() + timedelta(days=1),
        'iat': datetime.now()
    }
    SECRET_KEY = 'django-in'
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    serializer = AuthorSerializer(instance = author)
    response = Response()
    response.set_cookie(key='jwt', value=token, httponly=True)  
    response.data= {"jwt":token,"author":serializer.data}
    
    return response

@api_view(['POST'])
def signup(request):
    serializer = AuthorSerializer(data = request.data, partial= True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status= status.HTTP_201_CREATED)

    return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_author_from_cookie(request):
    token = request.COOKIES.get('jwt')
    if not token:
        return AuthenticationFailed("Unauthenticated")
    
    try:
        payload = jwt.decode(token, 'django-in', algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return AuthenticationFailed("Unauthenticated")
    
    author = Author.objects.filter(display_name = payload['id']).first()
    serializer = AuthorSerializer(instance = author)
    return Response(serializer.data)

@api_view(['POST'])
def logout(request):
    response = Response()
    response.delete_cookie('jwt')
    response.data = {
        "message": "success"
    }
    return response


