from django.urls import path
from . import views

urlpatterns = [
    path("", views.post, name="create_post"),
    path("create/", views.create_post, name="create"),
    path('editpost/', views.edit_post, name='edit_post'),
]