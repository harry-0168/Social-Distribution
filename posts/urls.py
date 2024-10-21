from django.urls import path
from . import views

urlpatterns = [
    path("", views.post, name="create_post"),
    path("create/", views.create_post, name="create"),
    path('<uuid:id>/editpost/', views.edit_post, name='edit_post'),
    path("<uuid:id>/viewPost/", views.view_post, name="viewPost"), # path to the specific post
    path("<uuid:id>/viewPost/likes/", views.view_postLikes, name="likes"), # path to posts view likes

    path("<uuid:id>/viewPost/repost_post/", views.repost_post, name="repost_post"),  # URL for repost functionality
    path("<uuid:id>/viewPost/repost_link/", views.repost_link, name="repost_link"),  # URL for repost functionality
    path("<uuid:id>/like/", views.like_post, name="like_post"),

    path('<uuid:id>/delete/', views.delete_post, name='delete_post'),

    # API paths for creating comments and likes
    path("<uuid:post_id>/comment/", views.create_comment, name="create_comment"),  # API for creating comments
    path("<uuid:post_id>/like/", views.create_like, name="create_like"),  # API for liking a post
]