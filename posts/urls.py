from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create_post, name="create"),
    path('post/<uuid:post_id>/', views.view_post, name='view_post'),

]