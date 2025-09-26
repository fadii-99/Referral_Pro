import json
import logging
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.apps import apps
from django.contrib.auth import get_user_model
User = get_user_model()
logger = logging.getLogger(__name__)
from chat.models import ChatRoom, ChatParticipant, Message, MessageReadStatus
from utils.storage_backends import generate_presigned_url
# ---------------------------------------------
# ChatConsumer
# ---------------------------------------------
class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling chat messages between users
    Supports rep-solo and company-solo conversations with company oversight
    """

    async def connect(self):
        """Handle WebSocket connection"""
        try:
            self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
            self.room_group_name = f"chat_{self.room_id}"
            self.user = self.scope.get("user")

            if not self.user or self.user.is_anonymous:
                await self.close(code=4001)
                return

            can_join = await self.can_user_join_room()
            if not can_join:
                await self.close(code=4003)
                return

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            await self.update_user_online_status(True)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_joined",
                    "user_id": self.user.id,
                    "user_name": self.user.full_name,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.info(f"User {self.user.id} connected to chat room {self.room_id}")

        except Exception as e:
            logger.error(f"Error in chat connect: {str(e)}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        try:
            await self.update_user_online_status(False)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_left",
                    "user_id": self.user.id,
                    "user_name": self.user.full_name,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            logger.info(f"User {self.user.id} disconnected from chat room {self.room_id}")

        except Exception as e:
            logger.error(f"Error in chat disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type", "chat_message")

            if message_type == "chat_message":
                await self.handle_chat_message(data)
            elif message_type == "typing":
                await self.handle_typing_indicator(data)
            elif message_type == "mark_read":
                await self.handle_mark_read(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"type": "error", "message": "Invalid message format"}))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({"type": "error", "message": "Server error"}))

    async def handle_chat_message(self, data):
        try:
            content = data.get("message", "").strip()
            message_type = data.get("message_type", "text")
            file_data = data.get("file_data", {})
            reply_to_id = data.get("reply_to")
            
            # Validate message content based on type
            if message_type == "text" and not content:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "Text messages cannot be empty"
                }))
                return
            
            if message_type in ["image", "video", "audio", "document", "file"] and not file_data.get("file_url"):
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"{message_type.title()} messages require file data"
                }))
                return

            can_send = await self.can_user_send_message()
            if not can_send:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "You do not have permission to send messages in this room"
                }))
                return

            # Handle reply validation
            reply_to_message = None
            if reply_to_id:
                reply_to_message = await self.get_reply_message(reply_to_id)
                if not reply_to_message:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Reply message not found"
                    }))
                    return

            # Create the message
            message = await self.save_message(
                content=content,
                message_type=message_type,
                file_data=file_data,
                reply_to=reply_to_message
            )

            # Send to chat room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message_id": message.id,
                    "message": content,
                    "sender_id": self.user.id,
                    "sender_name": self.user.full_name,
                    "sender_role": self.user.role,
                    "message_type": message.message_type,
                    "timestamp": message.created_at.isoformat(),
                    "file_url": message.file_url,
                    "file_name": message.file_name,
                    "file_size": message.file_size,
                    "file_type": message.file_type,
                    "duration": message.duration,
                    "thumbnail_url": message.thumbnail_url,
                    "dimensions": message.dimensions,
                    "reply_to": {
                        "id": message.reply_to.id,
                        "content": message.reply_to.content[:50],
                        "sender_name": message.reply_to.sender.full_name
                    } if message.reply_to else None,
                },
            )

            # Note: Real-time chat list updates are now handled automatically in the Message.save() method

        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            await self.send(text_data=json.dumps({
                "type": "error", 
                "message": "Failed to send message"
            }))

    async def handle_typing_indicator(self, data):
        try:
            is_typing = data.get("is_typing", False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": self.user.id,
                    "user_name": self.user.full_name,
                    "is_typing": is_typing,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error handling typing indicator: {str(e)}")

    async def handle_mark_read(self, data):
        try:
            message_id = data.get("message_id")
            if message_id:
                await self.mark_message_read(message_id)
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")

    # Outgoing events
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_indicator(self, event):
        if event["user_id"] != self.user.id:
            await self.send(text_data=json.dumps(event))

    async def user_joined(self, event):
        if event["user_id"] != self.user.id:
            await self.send(text_data=json.dumps(event))

    async def user_left(self, event):
        if event["user_id"] != self.user.id:
            await self.send(text_data=json.dumps(event))

    # Database operations
    @database_sync_to_async
    def can_user_join_room(self):
        ChatRoom = apps.get_model("chat", "ChatRoom")
        try:
            chat_room = ChatRoom.objects.get(room_id=self.room_id)
            return chat_room.can_user_participate(self.user)
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def can_user_send_message(self):
        ChatRoom = apps.get_model("chat", "ChatRoom")
        ChatParticipant = apps.get_model("chat", "ChatParticipant")
        try:
            chat_room = ChatRoom.objects.get(room_id=self.room_id)
            participant = ChatParticipant.objects.filter(chat_room=chat_room, user=self.user).first()
            return participant.can_send_messages if participant else chat_room.can_user_participate(self.user)
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content, message_type="text", file_data=None, reply_to=None):
        ChatRoom = apps.get_model("chat", "ChatRoom")
        Message = apps.get_model("chat", "Message")
        chat_room = ChatRoom.objects.get(room_id=self.room_id)
        
        message_data = {
            'chat_room': chat_room,
            'sender': self.user,
            'content': content,
            'message_type': message_type,
            'reply_to': reply_to
        }
        
        # Add file data if present
        if file_data:
            message_data.update({
                'file_url': file_data.get('file_url'),
                'file_name': file_data.get('file_name'),
                'file_size': file_data.get('file_size'),
                'file_type': file_data.get('file_type'),
                'duration': file_data.get('duration'),
                'thumbnail_url': file_data.get('thumbnail_url'),
                'dimensions': file_data.get('dimensions'),
            })
        
        return Message.objects.create(**message_data)
    
    @database_sync_to_async
    def get_reply_message(self, message_id):
        Message = apps.get_model("chat", "Message")
        try:
            ChatRoom = apps.get_model("chat", "ChatRoom")
            chat_room = ChatRoom.objects.get(room_id=self.room_id)
            return Message.objects.get(id=message_id, chat_room=chat_room)
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_message_read(self, message_id):
        Message = apps.get_model("chat", "Message")
        MessageReadStatus = apps.get_model("chat", "MessageReadStatus")
        try:
            message = Message.objects.get(id=message_id)
            read_status, created = MessageReadStatus.objects.get_or_create(message=message, user=self.user)
            return read_status
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def update_user_online_status(self, is_online):
        ChatRoom = apps.get_model("chat", "ChatRoom")
        ChatParticipant = apps.get_model("chat", "ChatParticipant")
        try:
            chat_room = ChatRoom.objects.get(room_id=self.room_id)
            participant, created = ChatParticipant.objects.get_or_create(
                chat_room=chat_room,
                user=self.user,
                defaults={"is_online": is_online},
            )
            if not created:
                participant.is_online = is_online
                participant.save(update_fields=["is_online", "last_seen_at"])
        except ChatRoom.DoesNotExist:
            pass


# ---------------------------------------------
# NotificationConsumer
# ---------------------------------------------
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
            self.user = self.scope.get("user")

            if not self.user or self.user.is_anonymous or str(self.user.id) != self.user_id:
                await self.close(code=4001)
                return

            self.notification_group_name = f"notifications_{self.user_id}"
            await self.channel_layer.group_add(self.notification_group_name, self.channel_name)
            await self.accept()

            logger.info(f"User {self.user_id} connected to notifications")
        except Exception as e:
            logger.error(f"Error in notification connect: {str(e)}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.notification_group_name, self.channel_name)
            logger.info(f"User {self.user_id} disconnected from notifications")
        except Exception as e:
            logger.error(f"Error in notification disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            _ = json.loads(text_data)
            # No-op for now
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in notifications")
        except Exception as e:
            logger.error(f"Error in notification receive: {str(e)}")

    async def new_message_notification(self, event):
        await self.send(text_data=json.dumps(event))

    async def referral_notification(self, event):
        await self.send(text_data=json.dumps(event))


# ---------------------------------------------
# ChatListConsumer
# ---------------------------------------------
class ChatListConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def get_user_chat_rooms(self):
        ChatRoom = apps.get_model("chat", "ChatRoom")
        ChatParticipant = apps.get_model("chat", "ChatParticipant")
        
        if not self.user or self.user.is_anonymous:
            print("⚠️ Cannot get chat rooms for anonymous user")
            return []
        
        from django.db.models import Q
        
        # Query chat rooms based on user role and relationships
        if self.user.role == 'solo':
            chat_rooms = ChatRoom.objects.filter(solo_user=self.user)
        elif self.user.role == 'employee':
            chat_rooms = ChatRoom.objects.filter(rep_user=self.user)
        elif self.user.role == 'company':
            # Company can see rooms where they are direct participants
            # or rooms where their reps are participants
            chat_rooms = ChatRoom.objects.filter(
                Q(company_user=self.user) | 
                Q(rep_user__parent_company=self.user)
            )
        else:
            chat_rooms = ChatRoom.objects.none()
        
        # Optimize queries with select_related
        chat_rooms = chat_rooms.select_related(
            'solo_user', 'rep_user', 'company_user', 'referral'
        ).prefetch_related(
            'messages', 'participants'
        ).distinct().order_by('-last_message_at')
        
        return [
            {
                "room_id": room.room_id,
                "room_type": room.room_type,
                "chat_name": room.get_display_name(self.user),
                "last_message": room.get_last_message_summary(),
                "unread_count": room.get_unread_count(self.user),
                "is_online": room.is_any_participant_online(exclude_user=self.user),
                "is_active": room.is_active,
                "created_at": room.created_at.isoformat(),
                "updated_at": room.updated_at.isoformat(),
                "referral_id": room.referral.reference_id if room.referral else None,
                "image_url": generate_presigned_url(f"media/{room.get_chat_image(self.user)}", expires_in=3600),
            }
            for room in chat_rooms
        ]

    @database_sync_to_async
    def get_user_profile_info(self):
        """Get additional user profile information"""
        if not self.user or self.user.is_anonymous:
            return {}
        
        return {
            "id": self.user.id,
            "username": getattr(self.user, 'username', ''),
            "email": getattr(self.user, 'email', ''),
            "full_name": getattr(self.user, 'full_name', str(self.user)),
            "role": getattr(self.user, 'role', ''),
            "is_active": getattr(self.user, 'is_active', True),
        }
    async def connect(self):
        print("🔌 WS connect attempt:", self.scope["path"])
        self.user = self.scope.get("user")
        
        # Require authentication for chat list access
        if not self.user or self.user.is_anonymous:
            print("⚠️ Unauthenticated user attempting to connect - closing connection")
            await self.close(code=4001)  # Unauthorized
            return

        self.group_name = f"chat_list_{self.user.id}"
            
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        
        # Get user's chat rooms and profile info from database
        chat_rooms = await self.get_user_chat_rooms()
        user_profile = await self.get_user_profile_info()
        
        
        await self.send(text_data=json.dumps({
            "type": "chat_rooms_loaded",
            "user_profile": user_profile,
            "chat_rooms": chat_rooms,
            "timestamp": datetime.now().isoformat()
        }))
        print(f"✅ WebSocket connection accepted. Group: {self.group_name}")

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            print(f"🔌 WebSocket disconnected from group: {self.group_name}")

    async def chat_list_update(self, event):
        await self.send(text_data=json.dumps(event))


# ---------------------------------------------
# Utility: Send notification to user
# ---------------------------------------------
@database_sync_to_async
def send_notification_to_user(user_id, notification_type, data):
    from channels.layers import get_channel_layer
    import asyncio

    channel_layer = get_channel_layer()
    asyncio.create_task(
        channel_layer.group_send(
            f"notifications_{user_id}",
            {"type": notification_type, **data},
        )
    )
