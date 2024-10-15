from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create_post, name="create"),
    path('editpost/', views.edit_post, name='edit_post'),
]