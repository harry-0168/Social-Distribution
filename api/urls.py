from django.urls import path
from posts.views import get_edit_delete_post,get_posts_create_post

urlpatterns = [
    path('authors/<uuid:author_id>/posts/<uuid:post_id>', get_edit_delete_post, name='edit_post'), # API for editing post
    path('authors/<uuid:author_id>/posts/', get_posts_create_post, name='get_posts'),
    path("authors/<uuid:author_id>/posts/", get_posts_create_post, name="create"),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>', get_edit_delete_post, name='delete_post'),
]