from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^api/ws/chat/(?P<room_id>[\w-]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'^api/ws/notifications/(?P<user_id>\d+)/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'^api/ws/chat-list/?$', consumers.ChatListConsumer.as_asgi()),
]


