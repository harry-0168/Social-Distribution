from django.urls import path
from . import views

urlpatterns = [
    # Admin views for rendering HTML templates
    path("", views.manage_dashboard, name='manage_dashboard'),
    path('authors/', views.manage_authors, name='manage_authors'),  
    path('notifications/', views.manage_notifications, name='manage_notifications'),
    path('posts/', views.manage_posts, name='manage_posts'),
    path('nodes/', views.manage_nodes, name='manage_nodes'),
    path('settings/', views.manage_settings, name='manage_settings'),

    # API endpoints for handling JSON responses
    path('api/authors/', views.api_list_authors, name='api_list_authors'), 
    path('api/authors/add/', views.api_add_author, name='api_add_author'),  
    path('api/authors/<int:author_id>/', views.api_author_detail, name='api_author_detail'),  
    path('api/authors/<int:author_id>/delete/', views.api_delete_author, name='api_delete_author'), 
]