from django.urls import path
from posts.views import get_edit_delete_post,get_posts_create_post
from author.views import api_list_authors, api_add_author, api_author_detail, login, signup, get_author_from_cookie, logout
from inbox.views import get_followers, get_following
from inbox.views import handle_follow_request_response, inboxApi

urlpatterns = [
    path('signup', signup, name='signup'),
    path('login', login, name='login'),
    path('author', get_author_from_cookie, name='get_author_from_cookie'),
    path('logout', logout, name='logout'),

    path("authors/<uuid:object_author_id>/inbox/", inboxApi, name="follow_request"), # sender of the follow request
    path("authors/<uuid:author_id>/followers" , get_followers, name="get_followers"), # get followers of an author
    path("authors/<uuid:author_id>/following" , get_following, name="get_following"), # get following of an author
    path("authors/<uuid:author_id>/followers/<path:foreign_author_fqid>", handle_follow_request_response, name="follow_request_response"), # receiver of the follow request, replies to the follow request
    
    path('authors/<uuid:author_id>/posts/<uuid:post_id>', get_edit_delete_post, name='edit_post'), # API for editing post
    path('authors/<uuid:author_id>/posts/', get_posts_create_post, name='get_posts'),
    path("authors/<uuid:author_id>/posts/", get_posts_create_post, name="create"),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>', get_edit_delete_post, name='delete_post'),
    
    # Author API endpoints
    path('authors/', api_list_authors, name='api_list_authors'), 
    path('authors/add/', api_add_author, name='api_add_author'),  
    path('authors/<uuid:author_id>/', api_author_detail, name='api_author_detail'),  
]