import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

asgi_app = get_asgi_application()

from .channels_middleware import JWTAuthMiddleware
from system.consumers import ChatConsumer


application = ProtocolTypeRouter({
    "http": asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            [path('ws/chat/', ChatConsumer.as_asgi())]
        )
    )
})
