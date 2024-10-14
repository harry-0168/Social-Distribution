from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Author, FollowRequest
from .serializers import AuthorSerializer, FollowRequestSerializer
from django.http import Http404

class AuthorPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 500

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = AuthorPagination

    def send_follow_request(self, request, pk=None):
        # Manually get the object_author using the 'pk' from URL
        try:
            object_author = Author.objects.get(pk=pk)
        except Author.DoesNotExist:
            return Response({"detail": "Object author not found."}, status=status.HTTP_404_NOT_FOUND)

        actor_author_data = request.data.get("actor")
        if not actor_author_data:
            return Response({"detail": "Missing actor data."}, status=status.HTTP_400_BAD_REQUEST)

        # Find the actor author
        try:
            actor_author = Author.objects.get(id=actor_author_data['id'])
        except Author.DoesNotExist:
            return Response({"detail": "Actor author not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create a follow request object
        follow_request = FollowRequest(
            actor=actor_author,
            object_author=object_author,
            summary=f"{actor_author.display_name} wants to follow {object_author.display_name}"
        )
        follow_request.save()

        serializer = FollowRequestSerializer(follow_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    def list_inbox(self, request, pk=None):
        # Get the author (object_author) whose inbox we are fetching
        try:
            object_author = Author.objects.get(pk=pk)
        except Author.DoesNotExist:
            return Response({"detail": "Author not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get all follow requests where the current author is the object_author
        follow_requests = FollowRequest.objects.filter(object_author=object_author)
        serializer = FollowRequestSerializer(follow_requests, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
