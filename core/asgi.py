# """
# ASGI config for core project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
# """

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# application = get_asgi_application()


import os
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from raffle import routing as raffle_routing
# # from accounts import routing as account_routing
# from .middleware import CustomWebSocketMiddleware 

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