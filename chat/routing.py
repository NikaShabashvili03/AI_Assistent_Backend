from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/conversation/update/$", consumers.ConversationConsumer.as_asgi()),
]