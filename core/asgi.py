import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') 

import django
django.setup() 

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat import routing
from .middleware import CustomWebSocketMiddleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": CustomWebSocketMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        ),
    )
})