from django.shortcuts import render
from .models import Notification

# Create your views here.
def inbox(request):
    notifications = Notification.objects.all()
    return render(request, 'inbox/inbox.html', {'notifications': notifications})