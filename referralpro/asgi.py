import os
import django
from django.core.asgi import get_asgi_application

# Configure Django settings before importing anything that might use models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'referralpro.settings')
django.setup()

# Import channels and other Django-dependent modules after setup
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.middleware import TokenAuthMiddleware
import chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(chat.routing.websocket_urlpatterns)
        )
    ),
})
