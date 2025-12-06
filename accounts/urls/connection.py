from django.urls import path
from ..views.connection import (
    SendConnectionRequest,
    AcceptConnectionRequest,
    DeclineConnectionRequest,
    ListConnections,
    SuggestedConnections,
    ReceivedConnectionRequests
)

urlpatterns = [
    path("request/send/<int:user_id>", SendConnectionRequest.as_view()),
    path("request/accept/<int:request_id>", AcceptConnectionRequest.as_view()),
    path("request/decline/<int:request_id>", DeclineConnectionRequest.as_view()),
    path('request/received', ReceivedConnectionRequests.as_view()),
    path("list", ListConnections.as_view()),
    path('suggestions', SuggestedConnections.as_view()), 
]
