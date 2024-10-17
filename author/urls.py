from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, profile_view, author_about, user_settings
from posts import views as post_views


router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')

urlpatterns = [
    path('api/', include(router.urls)),  
    
    # Public profile page for an author
    path('<int:author_id>/', profile_view, name='author_profile'),
    
    # About page for an author
    path('<int:author_id>/about/', author_about, name='author-about'),

    path('<int:author_id>/settings', user_settings, name= 'user-settings' )
]
