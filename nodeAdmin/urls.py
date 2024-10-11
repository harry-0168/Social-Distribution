from django.urls import path
from . import views

urlpatterns = [
    # URL pattern to render the admin dashboard
    path("", views.manage_dashboard, name='manage_dashboard'),
    path('authors/', views.manage_authors, name='manage_authors'),
    path('notifications/', views.manage_notifications, name='manage_notifications'),
    path('posts/', views.manage_posts, name='manage_posts'),
    path('nodes/', views.manage_nodes, name='manage_nodes'),
    path('settings/', views.manage_settings, name='manage_settings'),
]