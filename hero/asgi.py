import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from .channels_middleware import JWTAuthMiddleware

from system.consumers import ChatConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hero.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            [path('ws/chat/', ChatConsumer.as_asgi())]
        )
    )
})
