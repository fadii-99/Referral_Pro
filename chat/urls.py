from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Chat room management
    path('rooms/', views.ChatRoomListView.as_view(), name='chat_room_list'),
    path('rooms/create/', views.CreateChatRoomView.as_view(), name='create_chat_room'),
    path('rooms/<str:room_id>/', views.ChatRoomDetailView.as_view(), name='chat_room_detail'),
    path('rooms/<str:room_id>/update/', views.UpdateChatRoomView.as_view(), name='update_chat_room'),
    
    # Messaging
    path('rooms/<str:room_id>/messages/', views.SendMessageView.as_view(), name='send_message'),
    
    # Analytics
    path('analytics/', views.ChatAnalyticsView.as_view(), name='chat_analytics'),
]