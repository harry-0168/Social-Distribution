from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'authors', views.AuthorViewSet, basename='author')

urlpatterns = [
    path('api/', include(router.urls)),
    path('login', views.login, name='login'),
    path('signup', views.signup, name='signup'),
    path('test_token', views.test_token, name='test_token')
    
]
