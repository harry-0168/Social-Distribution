from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('private/', views.private_home_page, name='private_home_page'),
]