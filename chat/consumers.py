import json
import logging
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from .models import ChatRoom, Message, MessageReadStatus, ChatParticipant

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling chat messages between users
    Supports rep-solo and company-solo conversations with company oversight
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Get room ID from URL
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = f'chat_{self.room_id}'
            
            # Get user from scope (requires authentication middleware)
            self.user = self.scope.get('user')
            
            if not self.user or self.user.is_anonymous:
                await self.close(code=4001)
                return
            
            # Verify user can join this room
            can_join = await self.can_user_join_room()
            if not can_join:
                await self.close(code=4003)
                return
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Accept WebSocket connection
            await self.accept()
            
            # Update user's online status
            await self.update_user_online_status(True)
            
            # Notify other users that this user joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': self.user.id,
                    'user_name': self.user.full_name,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"User {self.user.id} connected to chat room {self.room_id}")
            
        except Exception as e:
            logger.error(f"Error in chat connect: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            # Update user's online status
            await self.update_user_online_status(False)
            
            # Notify other users that this user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'user_name': self.user.full_name,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            logger.info(f"User {self.user.id} disconnected from chat room {self.room_id}")
            
        except Exception as e:
            logger.error(f"Error in chat disconnect: {str(e)}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing_indicator(data)
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Server error'
            }))
    
    async def handle_chat_message(self, data):
        """Handle chat message sending"""
        try:
            content = data.get('message', '').strip()
            if not content:
                return
            
            # Check if user can send messages in this room
            can_send = await self.can_user_send_message()
            if not can_send:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'You do not have permission to send messages in this room'
                }))
                return
            
            # Save message to database
            message = await self.save_message(content, data.get('message_type', 'text'))
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'message': content,
                    'sender_id': self.user.id,
                    'sender_name': self.user.full_name,
                    'sender_role': self.user.role,
                    'message_type': message.message_type,
                    'timestamp': message.created_at.isoformat(),
                    'file_url': message.file_url,
                    'file_name': message.file_name
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to send message'
            }))
    
    async def handle_typing_indicator(self, data):
        """Handle typing indicator"""
        try:
            is_typing = data.get('is_typing', False)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'user_name': self.user.full_name,
                    'is_typing': is_typing,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling typing indicator: {str(e)}")
    
    async def handle_mark_read(self, data):
        """Handle marking messages as read"""
        try:
            message_id = data.get('message_id')
            if message_id:
                await self.mark_message_read(message_id)
                
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
    
    # WebSocket message handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'sender_role': event['sender_role'],
            'message_type': event['message_type'],
            'timestamp': event['timestamp'],
            'file_url': event.get('file_url'),
            'file_name': event.get('file_name')
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator to the sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
                'timestamp': event['timestamp']
            }))
    
    async def user_joined(self, event):
        """Send user joined notification to WebSocket"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'timestamp': event['timestamp']
            }))
    
    async def user_left(self, event):
        """Send user left notification to WebSocket"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'timestamp': event['timestamp']
            }))
    
    # Database operations
    @database_sync_to_async
    def can_user_join_room(self):
        """Check if user can join the chat room"""
        try:
            chat_room = ChatRoom.objects.get(room_id=self.room_id)
            return chat_room.can_user_participate(self.user)
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def can_user_send_message(self):
        """Check if user can send messages in this room"""
        try:
            chat_room = ChatRoom.objects.get(room_id=self.room_id)
            participant = ChatParticipant.objects.filter(
                chat_room=chat_room,
                user=self.user
            ).first()
            
            if participant:
                return participant.can_send_messages
            
            # If no explicit participant record, check if they can participate at all
            return chat_room.can_user_participate(self.user)
            
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, message_type='text'):
        """Save message to database"""
        try:
            chat_room = ChatRoom.objects.get(room_id=self.room_id)
            message = Message.objects.create(
                chat_room=chat_room,
                sender=self.user,
                content=content,
                message_type=message_type
            )
            return message
        except ChatRoom.DoesNotExist:
            raise Exception("Chat room not found")
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read by user"""
        try:
            message = Message.objects.get(id=message_id)
            read_status, created = MessageReadStatus.objects.get_or_create(
                message=message,
                user=self.user
            )
            return read_status
        except Message.DoesNotExist:
            pass
    
    @database_sync_to_async
    def update_user_online_status(self, is_online):
        """Update user's online status in the chat room"""
        try:
            chat_room = ChatRoom.objects.get(room_id=self.room_id)
            participant, created = ChatParticipant.objects.get_or_create(
                chat_room=chat_room,
                user=self.user,
                defaults={'is_online': is_online}
            )
            if not created:
                participant.is_online = is_online
                participant.save(update_fields=['is_online', 'last_seen_at'])
        except ChatRoom.DoesNotExist:
            pass


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time notifications
    """
    
    async def connect(self):
        """Handle WebSocket connection for notifications"""
        try:
            # Get user ID from URL
            self.user_id = self.scope['url_route']['kwargs']['user_id']
            self.user = self.scope.get('user')
            
            # Verify user authentication and authorization
            if not self.user or self.user.is_anonymous or str(self.user.id) != self.user_id:
                await self.close(code=4001)
                return
            
            # Create notification group for this user
            self.notification_group_name = f'notifications_{self.user_id}'
            
            # Join notification group
            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )
            
            # Accept WebSocket connection
            await self.accept()
            
            logger.info(f"User {self.user_id} connected to notifications")
            
        except Exception as e:
            logger.error(f"Error in notification connect: {str(e)}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            # Leave notification group
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
            
            logger.info(f"User {self.user_id} disconnected from notifications")
            
        except Exception as e:
            logger.error(f"Error in notification disconnect: {str(e)}")
    
    async def receive(self, text_data):
        """Handle incoming notification WebSocket messages"""
        try:
            data = json.loads(text_data)
            # Handle notification-specific messages if needed
            pass
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in notifications")
        except Exception as e:
            logger.error(f"Error in notification receive: {str(e)}")
    
    # Notification message handlers
    async def new_message_notification(self, event):
        """Send new message notification"""
        await self.send(text_data=json.dumps({
            'type': 'new_message_notification',
            'chat_room_id': event['chat_room_id'],
            'sender_name': event['sender_name'],
            'message_preview': event['message_preview'],
            'timestamp': event['timestamp']
        }))
    
    async def referral_notification(self, event):
        """Send referral-related notification"""
        await self.send(text_data=json.dumps({
            'type': 'referral_notification',
            'referral_id': event['referral_id'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))



# consumers.py
class ChatListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("🔌 WS connect attempt:", self.scope["path"])
        self.user = self.scope["user"]
        if not self.user or self.user.is_anonymous:
            await self.close(code=4001)
            return
        self.group_name = f"chat_list_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_list_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_list_update",
            "chat_rooms": event["chat_rooms"],
        }))



# Utility functions for sending notifications
@database_sync_to_async
def send_notification_to_user(user_id, notification_type, data):
    """Send notification to a specific user"""
    from channels.layers import get_channel_layer
    import asyncio
    
    channel_layer = get_channel_layer()
    notification_group_name = f'notifications_{user_id}'
    
    asyncio.create_task(
        channel_layer.group_send(
            notification_group_name,
            {
                'type': notification_type,
                **data
            }
        )
    )