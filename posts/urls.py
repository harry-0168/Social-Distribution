from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create_post, name="create"),
    path("viewPost/", views.view_post, name="view"), # path to the specific post TODO: make redirection to specific postID
    # path("page/<int:id>/likes/", views.view_postLikes, name="likes") # path to posts view likes
]