from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('api/authors/<uuid:author_id>/posts/', views.get_posts, name='get_posts'),
]