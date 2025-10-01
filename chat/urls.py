from django.urls import path
from . import views
from .upload_views import MediaUploadView, VoiceMessageUploadView, ImagePreviewView

app_name = 'chat'

urlpatterns = [
    # Chat room management
    path('rooms/', views.ChatRoomListView.as_view(), name='chat_room_list'),
    path('rooms/create/', views.CreateChatRoomView.as_view(), name='create_chat_room'),
    path('rooms/<str:room_id>/', views.ChatRoomDetailView.as_view(), name='chat_room_detail'),
    path('rooms/<str:room_id>/update/', views.UpdateChatRoomView.as_view(), name='update_chat_room'),
    
    # Messaging
    path('rooms/<str:room_id>/messages/', views.SendMessageView.as_view(), name='send_message'),
    path('rooms/<str:room_id>/mark-read/', views.MarkMessagesReadView.as_view(), name='mark_messages_read'),
    path('rooms/<str:room_id>/mark-all-read/', views.MarkAllMessagesReadView.as_view(), name='mark_all_messages_read'),
    
    # File uploads
    path('upload/media/', MediaUploadView.as_view(), name='upload_media'),
    path('upload/voice/', VoiceMessageUploadView.as_view(), name='upload_voice'),
    path('upload/preview/', ImagePreviewView.as_view(), name='image_preview'),
    
    # Analytics
    path('analytics/', views.ChatAnalyticsView.as_view(), name='chat_analytics'),
]