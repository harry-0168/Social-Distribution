from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, profile_view, author_about, login, signup, get_author_from_cookie, logout, user_settings
from posts import views as post_views


router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')  # Registers /authors/ endpoint

urlpatterns = [

    path('api/', include(router.urls)),  
    path('login', login, name='login'),
    path('signup', signup, name='signup'),
    path('author', get_author_from_cookie, name='get_author_from_cookie'),
    path('logout', logout, name='logout'),
    
    
    # Public profile page for an author
    path('<uuid:author_id>/', profile_view, name='author_profile'),
    
    # About page for an author
    path('<uuid:author_id>/about/', author_about, name='author-about'),
    path('authors/<int:pk>/inbox/', AuthorViewSet.as_view({'post': 'send_follow_request', 'get': 'list_inbox'})),  # Added GET for viewing inbox

    # Endpoint to handle follow requests
    path('authors/<int:author_id>/follow/', follow_author, name='follow-author'),
    path('authors/<int:author_id>/unfollow/', unfollow_author, name='unfollow-author'),
    
    # Routes for viewing lists of followers and following
    path('<int:author_id>/followers/', followers_list, name='followers_list'),
    path('<int:author_id>/following/', following_list, name='following_list'),

    path('<uuid:author_id>/settings', user_settings, name= 'user-settings' )
]
