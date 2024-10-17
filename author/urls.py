from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, profile_view, author_about
from posts import views as post_views

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')  # Registers /authors/ endpoint

urlpatterns = [

    path('api/', include(router.urls)),  
    
    # Public profile page for an author
    path('<int:author_id>/', profile_view, name='author_profile'),
    
    # About page for an author
    path('<int:author_id>/about/', author_about, name='author-about'),
    path('authors/<int:pk>/inbox/', AuthorViewSet.as_view({'post': 'send_follow_request', 'get': 'list_inbox'})),  # Added GET for viewing inbox

]
