from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from author.serializers import AuthorSerializer
from django.shortcuts import get_object_or_404
from author.models import Author

@api_view(['POST'])
def nodeSignup(request):
    '''
    API endpoint for nodes to sign up and authenticate
    '''
    if request.method == 'POST':
        # Node signup logic
        data = request.data
        data['displayName'] = data['username'] 
        data['isNode'] = True
        data['type'] = 'node' if 'type' not in data else data['type']
        data['host'] = f"http://{request.get_host()}" if 'host' not in data else data['host']

        serializer = AuthorSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
# @authentication_classes([BasicAuthentication]) 
# @permission_classes([IsAuthenticated])
def get_nodes(request):
    '''
    API endpoint for getting all nodes
    '''
    try:
        if request.method == 'GET':
            auth = BasicAuthentication()
            user, auth_status = auth.authenticate(request)
            if not user or not IsAuthenticated().has_permission(request, None):
                    return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            if not user.isNode:
                return Response({"error": "Not approved by admin"}, status=status.HTTP_403_FORBIDDEN)
            authors = Author.objects.all().filter(isNode=True)
            serializer = AuthorSerializer(authors, many=True)
            return Response(serializer.data)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
# @permission_classes([IsAdminUser])
def update_node_sharing(request, node_id):
    """
    API endpoint for an admin to update if to share with an existing node.
    """
    node = get_object_or_404(Author, id=node_id, isNode=True)

    if not node.isNode:
        return Response({"error": "This ID is not a node"}, status=status.HTTP_400_BAD_REQUEST)
    
    is_sharing = request.data.get("isSharedNode")
    if is_sharing is not None:
        node.isSharedNode = is_sharing
        node.save()
        return Response({"message": f"Node sharing status updated to {is_sharing}"}, status=status.HTTP_200_OK)

    return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
# @permission_classes([IsAdminUser])
def get_shared_nodes(request):
    """
    API endpoint to retrieve all nodes that we are currently sharing with (isSharedNode = True)
    """
    shared_nodes = Author.objects.filter(isNode=True, isSharedNode=True)
    
    serializer = AuthorSerializer(shared_nodes, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)