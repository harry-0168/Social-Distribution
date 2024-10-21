from django.urls import path
from . import views

urlpatterns = [

    path("", views.inbox, name="inbox"),
    path("api/authors/<uuid:object_author_id>/inbox/", views.inboxApi, name="inboxApi"),
    path("follow", views.handle_follow_request_response, name="follow_request_response"), # receiver of the follow request, replies to the follow request
]