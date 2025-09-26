# chat/middleware.py
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class TokenAuthMiddleware:
    """
    Custom token auth middleware for Django Channels
    Supports token passed in query string ?token=xxx OR in headers
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        return await TokenAuthMiddlewareInstance(scope, self)(receive, send)

class TokenAuthMiddlewareInstance:
    def __init__(self, scope, middleware):
        self.scope = dict(scope)
        self.inner = middleware.inner

    async def __call__(self, receive, send):
        # Set user in scope before passing to inner middleware
        self.scope["user"] = await self.get_user(self.scope)
        # Call the inner middleware with the full ASGI signature
        return await self.inner(self.scope, receive, send)

    @database_sync_to_async
    def get_user(self, scope):
        # Try to extract token
        headers = dict(scope.get("headers", []))
        query_string = parse_qs(scope.get("query_string", b"").decode())

        token = None
        if b"authorization" in headers:
            auth_header = headers[b"authorization"].decode()
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        elif "token" in query_string:
            token = query_string["token"][0]

        if not token:
            return AnonymousUser()

        try:
            access_token = AccessToken(token)
            user = User.objects.get(id=access_token["user_id"])
            return user
        except Exception:
            return AnonymousUser()
