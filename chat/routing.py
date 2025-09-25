from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # WebSocket URL for chat rooms
    # Format: ws://localhost:8000/ws/chat/{room_id}/
    re_path(r'ws/chat/(?P<room_id>[\w-]+)/$', consumers.ChatConsumer.as_asgi()),
    
    # WebSocket URL for user notifications
    # Format: ws://localhost:8000/ws/notifications/{user_id}/
    re_path(r'ws/notifications/(?P<user_id>\d+)/$', consumers.NotificationConsumer.as_asgi()),
]