from django.urls import path
from posts.views import get_edit_delete_post,get_posts_create_post,get_post_image, api_create_like, api_view_postLikes, api_view_Likes
from author.views import api_list_authors, api_add_author, api_author_detail, login, signup, get_author_from_cookie, logout


urlpatterns = [
    path('signup', signup, name='signup'),
    path('login', login, name='login'),
    path('author', get_author_from_cookie, name='get_author_from_cookie'),
    path('logout', logout, name='logout'),

    path('authors/<uuid:author_id>/posts/<uuid:post_id>', get_edit_delete_post, name='edit_post'), # API for editing post
    path('authors/<uuid:author_id>/posts/', get_posts_create_post, name='get_posts'),
    path("authors/<uuid:author_id>/posts/", get_posts_create_post, name="create"),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>', get_edit_delete_post, name='delete_post'),
    
    path('posts/<str:FQID>/image/', get_post_image, name='post_image_FQID'),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/image', get_post_image, name='post_image_SERIAL'),

    # Author API endpoints
    path('authors/', api_list_authors, name='api_list_authors'), 
    path('authors/add/', api_add_author, name='api_add_author'),  
    path('authors/<uuid:author_id>/', api_author_detail, name='api_author_detail'), 
    
    # Post API endpoints
    path("authors/<uuid:author_id>/inbox", api_create_like, name="api_create_like"),  # API for liking a post
    path("authors/<uuid:author_id>/posts/<uuid:post_id>/likes", api_view_postLikes, name="api_likes"), # path to posts view likes
    path("posts/<uuid:post_id>/likes",api_view_Likes,name="api_view_Likes")
    

    
]