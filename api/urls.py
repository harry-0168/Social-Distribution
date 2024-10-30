from django.urls import path
from posts.views import get_edit_delete_post,get_posts_create_post
from author.views import api_list_authors, api_add_author, api_author_detail


urlpatterns = [
    path('authors/<uuid:author_id>/posts/<uuid:post_id>', get_edit_delete_post, name='edit_post'), # API for editing post
    path('authors/<uuid:author_id>/posts/', get_posts_create_post, name='get_posts'),
    path("authors/<uuid:author_id>/posts/", get_posts_create_post, name="create"),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>', get_edit_delete_post, name='delete_post'),
    
    # Author API endpoints
    path('api/authors/', api_list_authors, name='api_list_authors'), 
    path('api/authors/add/', api_add_author, name='api_add_author'),  
    path('api/authors/<uuid:author_id>/', api_author_detail, name='api_author_detail'),  
]