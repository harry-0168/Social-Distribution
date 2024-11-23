from django.urls import path, include,re_path
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, profile_view, author_about, loginPage, user_settings, follow_author,followers_list,following_list,unfollow_author
from posts.views import PostViewSet
from django.contrib.auth import views as auth_views
from . import views

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')  # Registers /authors/ endpoint
router.register(r'posts', PostViewSet, basename='post')  # Registers /posts/ endpoint

urlpatterns = [

    path('api/', include(router.urls)),  
    path('login/', loginPage, name='loginPage'),
    
    # Public profile page for an author
    path('<path:author_id>/', profile_view, name='author_profile'),
    
    # About page for an author
    path('<uuid:author_serial>/about/', author_about, name='author-about'),
    #path('authors/<int:pk>/inbox/', AuthorViewSet.as_view({'post': 'send_follow_request', 'get': 'list_inbox'})),  # Added GET for viewing inbox
    path('send_req/', AuthorViewSet.as_view({'post': 'send_follow_request'}), name='send-follow-request'),  # Added for sending follow request
    
    # Endpoint to handle follow requests
    path('authors/<uuid:object_author_serial>/follow/', follow_author, name='follow-author'),
    path('authors/<uuid:object_author_serial>/unfollow/', unfollow_author, name='unfollow-author'),

    # Routes for viewing lists of followers and following
    path('<uuid:author_serial>/followers/', followers_list, name='followers_list'),
    path('<uuid:author_serial>/following/', following_list, name='following_list'),

    # Route for user settings
    path('<uuid:author_serial>/settings', user_settings, name= 'user-settings' ),
    
    re_path(
        r'^(?P<author_serial>[0-9a-f-]+)/followers/(?P<foreign_author_id>.+)/$',
        views.manage_follower,
        name='manage_follower'
    ),

]
