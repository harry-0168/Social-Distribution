from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, profile_view, author_about, login, signup, get_author_from_cookie, logout
from posts import views as post_views

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')

urlpatterns = [
    path('api/', include(router.urls)),  
    path('login', login, name='login'),
    path('signup', signup, name='signup'),
    path('author', get_author_from_cookie, name='get_author_from_cookie'),
    path('logout', logout, name='logout'),
    
    
    # Public profile page for an author
    path('<int:author_id>/', profile_view, name='author_profile'),
    
    # About page for an author
    path('<int:author_id>/about/', author_about, name='author-about'),
]
