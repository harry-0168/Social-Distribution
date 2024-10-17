from django.urls import path
from . import views

urlpatterns = [
    path("", views.post, name="create_post"),
    path("create/", views.create_post, name="create"),
    path('<uuid:post_id>/delete/', views.delete_post, name='delete_post'),
    path('editpost/', views.edit_post, name='edit_post'),
    path("<uuid:id>/viewPost/", views.view_post, name="view"), # path to the specific post
    path("<uuid:id>/viewPost/likes/", views.view_postLikes, name="likes"), # path to posts view likes
    path("<uuid:id>/like/", views.like_post, name="like_post"),
]