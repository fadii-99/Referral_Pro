import json
import logging
from datetime import datetime
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.apps import apps
from django.contrib.auth import get_user_model
User = get_user_model()
logger = logging.getLogger(__name__)
from chat.models import ChatRoom, ChatParticipant, Message, MessageReadStatus
from utils.storage_backends import generate_presigned_url
from django.utils import timezone


# Custom JSON encoder that converts datetime → ISO string
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class BaseJsonConsumer(AsyncWebsocketConsumer):
    async def send_json(self, data):
        print("Chat rooms data in consumer:", data)
        await self.send(text_data=json.dumps(data, cls=DateTimeEncoder))


# ---------------------------------------------
# ChatConsumer
# ---------------------------------------------
class ChatConsumer(BaseJsonConsumer):
    """
    WebSocket consumer for handling chat messages between users
    Supports rep-solo and company-solo conversations with company oversight
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # typing state for THIS connection/user
        self._typing_task = None
        self._typing_active = False

    async def connect(self):
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
                    "timestamp": timezone.now().isoformat(),
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
                    "timestamp": datetime.now(),
                },
            )
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            logger.info(f"User {self.user.id} disconnected from chat room {self.room_id}")
        except Exception as e:
            logger.error(f"Error in chat disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            logger.debug(f"Received data: {text_data}")
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
            await self.send_json({"type": "error", "message": "Invalid message format"})
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send_json({"type": "error", "message": "Server error"})

    async def handle_chat_message(self, data):
        try:
            content = data.get("message", "").strip()
            message_type = data.get("message_type", "text")
            file_data = data.get("file_data", {})
            reply_to_id = data.get("reply_to")

            if message_type == "text" and not content:
                await self.send_json({"type": "error", "message": "Text messages cannot be empty"})
                return

            if message_type in ["image", "video", "audio", "document", "file"] and not file_data.get("file_url"):
                await self.send_json({"type": "error", "message": f"{message_type.title()} messages require file data"})
                return

            can_send = await self.can_user_send_message()
            if not can_send:
                await self.send_json({"type": "error", "message": "You do not have permission to send messages"})
                return

            reply_to_message = None
            if reply_to_id:
                reply_to_message = await self.get_reply_message(reply_to_id)
                if not reply_to_message:
                    await self.send_json({"type": "error", "message": "Reply message not found"})
                    return

            message = await self.save_message(
                content=content,
                message_type=message_type,
                file_data=file_data,
                reply_to=reply_to_message,
            )

            # Broadcast only identifiers; each recipient will serialize the message
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "room_id": self.room_id, "message_id": message.id},
            )

        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            await self.send_json({"type": "error", "message": "Failed to send message"})


    async def handle_typing_indicator(self, data):
        """
        Debounced/TTL typing indicator:
        - start: broadcast immediately, then schedule auto-stop after short idle window
        - subsequent keypresses: just reset the timer (no spam)
        - stop: broadcast immediately and cancel timer
        """
        try:
            is_typing = bool(data.get("is_typing", False))
            ttl_seconds = float(data.get("ttl", 1.2))  # allow client to override, default ~1.2s

            if is_typing:
                # Broadcast START only if not already active
                if not self._typing_active:
                    self._typing_active = True
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "typing_indicator",
                            "user_id": self.user.id,
                            "user_name": self.user.full_name,
                            "is_typing": True,
                            "timestamp": timezone.now().isoformat(),
                        },
                    )
                # Reset the idle timeout
                if self._typing_task and not self._typing_task.done():
                    self._typing_task.cancel()
                self._typing_task = asyncio.create_task(self._typing_timeout(ttl_seconds))

            else:
                # Explicit STOP from client: cancel timer and broadcast stop if active
                await self._typing_stop_broadcast()

        except Exception as e:
            logger.error(f"Error handling typing indicator: {str(e)}")

    async def _typing_timeout(self, delay: float):
        try:
            await asyncio.sleep(delay)
            await self._typing_stop_broadcast()
        except asyncio.CancelledError:
            # Keystroke arrived in time; just exit
            pass

    async def _typing_stop_broadcast(self):
        """Cancel timer and broadcast stop if we are currently active."""
        if self._typing_task and not self._typing_task.done():
            self._typing_task.cancel()
        if self._typing_active:
            self._typing_active = False
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": self.user.id,
                    "user_name": self.user.full_name,
                    "is_typing": False,
                    "timestamp": timezone.now().isoformat(),
                },
            )

    # keep your existing recipient-side event -> socket send
    async def typing_indicator(self, event):
        if event["user_id"] != self.user.id:
            # normalize payload (explicit type & ISO timestamp already set above)
            event["type"] = "typing"
            await self.send_json(event)

    async def handle_mark_read(self, data):
        try:
            message_id = data.get("message_id")
            if message_id:
                await self.mark_message_read(message_id)
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")

    # Outgoing events (all use safe encoder)

    async def chat_message(self, event):
        """
        Normalize to the SAME shape as API messages_data[] for this viewer.
        Accepts both:
        1) {"message_id": 123}
        2) {"message": {"id": 123, ...}}   # legacy producers
        """
        # --- Accept both new and legacy event shapes ---
        message_id = event.get("message_id")
        if not message_id:
            legacy_msg = event.get("message")
            if isinstance(legacy_msg, dict):
                message_id = legacy_msg.get("id")

        if not message_id:
            logger.error("WS chat_message event missing message_id (and legacy message.id). Ignoring.")
            return

        # --- Serialize to API shape for this viewer ---
        try:
            msg_obj = await self._serialize_message_for_client(message_id, self.user)
        except Exception as e:
            logger.exception(f"Failed to serialize message {message_id}: {e}")
            return

        # Add a routing type; rest matches API exactly
        msg_obj["type"] = "chat_message"
        await self.send_json(msg_obj)


    async def typing_indicator(self, event):
        if event["user_id"] != self.user.id:
            await self.send_json(event)

    async def user_joined(self, event):
        if event["user_id"] != self.user.id:
            await self.send_json(event)

    async def user_left(self, event):
        if event["user_id"] != self.user.id:
            await self.send_json(event)

    async def chat_list_update(self, event):
        # 🔑 FIX: Use safe encoder here
        await self.send_json(event)

    # Wrapper for safe JSON sending
    async def send_json(self, data):
        await self.send(text_data=json.dumps(data, cls=DateTimeEncoder))

    # DB operations
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
            "chat_room": chat_room,
            "sender": self.user,
            "content": content,
            "message_type": message_type,
            "reply_to": reply_to,
        }

        if file_data:
            message_data.update({
                "file_url": file_data.get("file_url"),
                "file_name": file_data.get("file_name"),
                "file_size": file_data.get("file_size"),
                "file_type": file_data.get("file_type"),
                "duration": file_data.get("duration"),
                "thumbnail_url": file_data.get("thumbnail_url"),
                "dimensions": file_data.get("dimensions"),
            })

        return Message.objects.create(**message_data)

    @database_sync_to_async
    def get_reply_message(self, message_id):
        Message = apps.get_model("chat", "Message")
        ChatRoom = apps.get_model("chat", "ChatRoom")
        try:
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
            read_status, _ = MessageReadStatus.objects.get_or_create(message=message, user=self.user)
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

    @database_sync_to_async
    def _serialize_message_for_client(self, message_id, viewer):
        Message = apps.get_model("chat", "Message")
        msg = (
            Message.objects
            .select_related("sender", "chat_room")
            .prefetch_related("read_statuses")
            .get(id=message_id)
        )

        sender_image_url = (
            generate_presigned_url(f"media/{msg.sender.image}", expires_in=3600)
            if getattr(msg.sender, "image", None) else None
        )

        return {
            "id": msg.id,
            "room_id": msg.chat_room.room_id,
            "sender": {
                "id": msg.sender.id,
                "name": msg.sender.full_name,
                "role": msg.sender.role,
                "image_url": sender_image_url,
            },
            "content": msg.content,
            "message_type": msg.message_type,
            "created_at": msg.created_at.isoformat(),
            "is_read": msg.read_statuses.filter(user=viewer).exists(),
            "read_by": list(msg.read_statuses.values_list("user_id", flat=True)),
        }

# ---------------------------------------------
# ChatListConsumer
# ---------------------------------------------

class ChatListConsumer(BaseJsonConsumer):
    """
    Sends the chat list in the SAME shape as the REST API:
    {
      "room_id", "room_type", "chat_name", "last_message",
      "unread_count", "is_online", "is_active",
      "created_at", "updated_at", "referral_id", "image_url"
    }
    """

    # ---------- Public WS lifecycle ----------

    async def connect(self):
        print("🔌 WS connect attempt:", self.scope["path"])
        self.user = self.scope.get("user")

        if not self.user or self.user.is_anonymous:
            print("⚠️ Unauthenticated user attempting to connect - closing connection")
            await self.close(code=4001)
            return

        self.group_name = f"chat_list_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Initial payload: API-shaped rooms list
        rooms_data = await self._fetch_and_serialize_rooms_for_user(self.user)
        user_profile = await self._get_user_profile_info()

        await self.send(text_data=json.dumps({
            "type": "chat_rooms_loaded",
            "user_profile": user_profile,
            "chat_rooms": rooms_data,
            "timestamp": datetime.now().isoformat()
        }, cls=DateTimeEncoder))

        print(f"✅ WebSocket connection accepted. Group: {self.group_name}")

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            print(f"🔌 WebSocket disconnected from group: {self.group_name}")

    # ---------- Incoming group event -> out to client ----------

    async def chat_list_update(self, event):
        """
        Always normalize to API shape before sending to the client.

        Supported inbound shapes from producers:
        1) {"type":"chat_list_update", "room_ids":[...]}
        2) {"type":"chat_list_update", "chat_rooms":[{"room_id": ...}, ...]}
        3) {"type":"chat_list_update"}  -> fallback to full reload for this user
        """
        room_ids = event.get("room_ids")

        if not room_ids and event.get("chat_rooms"):
            # producer sent full objects; extract room_ids safely
            objs = event["chat_rooms"]
            room_ids = []
            for o in objs:
                if isinstance(o, dict) and "room_id" in o:
                    room_ids.append(o["room_id"])

        if room_ids:
            rooms_data = await self._fetch_and_serialize_rooms_by_ids(room_ids, self.user)
        else:
            # fallback: reload all rooms for this user
            rooms_data = await self._fetch_and_serialize_rooms_for_user(self.user)

        await self.send_json({
            "type": "chat_list_update",
            "chat_rooms": rooms_data,
            "timestamp": timezone.now().isoformat()
        })

    # ---------- Private helpers (DB + serialization) ----------

    @database_sync_to_async
    def _serialize_room_for_list(self, room, viewer):
        """
        Mirrors the REST API response format exactly.
        """
        # get_display_name(viewer), get_last_message_summary(), get_unread_count(viewer),
        # is_any_participant_online(exclude_user=viewer), get_chat_image(viewer) are assumed
        # methods on ChatRoom, as in your API code.
        chat_image = room.get_chat_image(viewer)
        image_url = generate_presigned_url(f"media/{chat_image}", expires_in=3600) if chat_image else None

        return {
            "room_id": room.room_id,
            "room_type": room.room_type,
            "chat_name": room.get_display_name(viewer),
            "last_message": room.get_last_message_summary(),
            "unread_count": room.get_unread_count(viewer),
            "is_online": room.is_any_participant_online(exclude_user=viewer),
            "is_active": room.is_active,
            "created_at": room.created_at.isoformat(),
            "updated_at": room.updated_at.isoformat(),
            "referral_id": room.referral.reference_id if getattr(room, "referral", None) else None,
            "image_url": image_url,
        }

    @database_sync_to_async
    def _get_user_profile_info(self):
        """Same shape you already send on connect."""
        if not self.user or self.user.is_anonymous:
            return {}
        u = self.user
        return {
            "id": u.id,
            "username": getattr(u, 'username', ''),
            "email": getattr(u, 'email', ''),
            "full_name": getattr(u, 'full_name', str(u)),
            "role": getattr(u, 'role', ''),
            "is_active": getattr(u, 'is_active', True),
        }

    @database_sync_to_async
    def _query_rooms_for_user(self, viewer):
        ChatRoom = apps.get_model("chat", "ChatRoom")

        if viewer.role == 'solo':
            qs = ChatRoom.objects.filter(solo_user=viewer)
        elif viewer.role == 'employee':
            qs = ChatRoom.objects.filter(rep_user=viewer)
        elif viewer.role == 'company':
            qs = ChatRoom.objects.filter(Q(company_user=viewer) | Q(rep_user__parent_company=viewer))
        else:
            qs = ChatRoom.objects.none()

        qs = (qs
              .select_related('solo_user', 'rep_user', 'company_user', 'referral')
              .prefetch_related('messages', 'participants')
              .distinct()
              .order_by('-last_message_at'))
        return list(qs)

    @database_sync_to_async
    def _query_rooms_by_ids(self, room_ids):
        ChatRoom = apps.get_model("chat", "ChatRoom")
        qs = (ChatRoom.objects.filter(room_id__in=room_ids)
              .select_related('solo_user', 'rep_user', 'company_user', 'referral')
              .prefetch_related('messages', 'participants'))
        # Preserve input order if you care:
        ordered = {r.room_id: r for r in qs}
        return [ordered[rid] for rid in room_ids if rid in ordered]

    async def _fetch_and_serialize_rooms_for_user(self, viewer):
        rooms = await self._query_rooms_for_user(viewer)
        out = []
        for r in rooms:
            out.append(await self._serialize_room_for_list(r, viewer))
        return out

    async def _fetch_and_serialize_rooms_by_ids(self, room_ids, viewer):
        rooms = await self._query_rooms_by_ids(room_ids)
        out = []
        for r in rooms:
            out.append(await self._serialize_room_for_list(r, viewer))
        return out







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
