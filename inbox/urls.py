from django.urls import path
from . import views

urlpatterns = [

    path("", views.inbox, name="inbox"),
    path("api/authors/<uuid:object_author_id>/inbox/", views.inboxApi, name="inboxApi"),
]