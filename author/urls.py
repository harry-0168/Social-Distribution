from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, profile_view, author_about
from posts.views import PostViewSet

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')  # Registers /authors/ endpoint
router.register(r'posts', PostViewSet, basename='post')  # Registers /posts/ endpoint

urlpatterns = [
    path('api/', include(router.urls)),  # Ensure you have this line to route API calls correctly
    path('<int:author_id>/', profile_view, name='author_profile'),
    path('<int:author_id>/about/', author_about, name='author-about'),
    path('authors/<int:pk>/inbox/', AuthorViewSet.as_view({'post': 'send_follow_request', 'get': 'list_inbox'})),
]
