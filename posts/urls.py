from django.urls import path
from . import views

urlpatterns = [
    path("", views.post, name="create_post"),
    path("create/", views.create_post, name="create"),
    
    path('<uuid:post_id>/delete/', views.delete_post, name='delete_post'),
]