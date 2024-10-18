from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
import jwt
from .models import Notification
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from author.models import Author
from django.conf import settings

@api_view(['GET'])
def inbox(request):
    token = request.COOKIES.get('jwt')
    if not token:
        return Response({"error": "Unauthenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        payload = jwt.decode(token, 'django-in', algorithms=['HS256'])
        author = get_object_or_404(Author, display_name=payload['id'])
        notifications = Notification.objects.filter(author=author)
        return render(request, 'inbox/inbox.html', {'notifications': notifications})

    except jwt.ExpiredSignatureError:
        return Response({"error": "Unauthenticated"}, status=401)
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid token"}, status=401)
    except Author.DoesNotExist:
        return Response({"error": "Author not found"}, status=404)

