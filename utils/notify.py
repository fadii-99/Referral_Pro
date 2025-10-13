# utils/notify.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from django.db import connection, transaction

# ---------- internal helpers ----------

def _create_notifications_safely(model_cls, objs):
    """
    Create rows and guarantee .id is populated on returned objects.
    Uses bulk_create only if the backend can return rows from bulk insert.
    """
    if not objs:
        return []

    can_return_ids = getattr(connection.features, "can_return_rows_from_bulk_insert", False)

    if can_return_ids:
        # On backends like PostgreSQL this will populate primary keys.
        created = model_cls.objects.bulk_create(objs)
    else:
        # Fallback: save individually so .id is set.
        created = []
        with transaction.atomic():
            for o in objs:
                o.save()
                created.append(o)

    # Paranoid check: if any IDs are still None, refetch (rare, but just in case)
    if any(getattr(o, "id", None) is None for o in created):
        # Attempt a targeted refetch using a short time window.
        # NOTE: We cannot rely on .created_at from the object if it's auto_now_add at DB time,
        # so we refetch by a minimal set of constraints + a tight time window.
        # Callers should pass a qs to refine this further if needed.
        model_name = model_cls.__name__
        raise RuntimeError(
            f"{model_name}: bulk insert returned objects without IDs. "
            "Either your DB doesn't support returning IDs for bulk inserts or the model is misconfigured."
        )

    return created


def _group_by_user_id(notifications):
    by_user = {}
    for n in notifications:
        uid = n.user_id
        by_user.setdefault(uid, []).append(n)
    return by_user


def _serialize_notification(n, *, include_chat=False, include_referral=True):
    """Shape matches your API response structure."""
    # Only include relateds if present
    actor_user = None
    if n.actor_user_id and getattr(n, "actor_user", None):
        actor_user = {
            "id": n.actor_user.id,
            "full_name": getattr(n.actor_user, "full_name", None),
        }

    referral = None
    if include_referral and n.referral_id and getattr(n, "referral", None):
        referral = {
            "id": n.referral.id,
            "reference_id": getattr(n.referral, "reference_id", None),
            "service_type": getattr(n.referral, "service_type", ""),
            "status": getattr(n.referral, "status", None),
        }

    chat_room = None
    if include_chat and n.chat_room_id and getattr(n, "chat_room", None):
        chat_room = {
            "id": n.chat_room.id,
            "room_id": getattr(n.chat_room, "room_id", None),
            "room_type": getattr(n.chat_room, "room_type", None),
        }

    chat_message = None
    if include_chat and n.chat_message_id and getattr(n, "chat_message", None):
        mt = getattr(n.chat_message, "message_type", None)
        chat_message = {
            "id": n.chat_message.id,
            "message_type": mt,
            "content": (
                n.chat_message.content
                if mt == "text"
                else f"[{(mt or '').upper()}]"
            ),
        }

    return {
        "id": n.id,  # <-- now guaranteed not None
        "event_type": n.event_type,
        "title": n.title,
        "message": n.message,
        "is_read": getattr(n, "is_read", False),
        "created_at": n.created_at.isoformat() if hasattr(n, "created_at") else timezone.now().isoformat(),
        "meta_data": getattr(n, "meta_data", None),
        "actor_user": actor_user,
        "referral": referral,
        "chat_room": chat_room,
        "chat_message": chat_message,
    }

# ---------- public dispatchers ----------

def notify_users(user_ids, payload, event_type="notification"):
    event = payload.get("event", "") or ""
    if event.startswith("chat."):
        return notify_chat_users(user_ids, payload, "new_message_notification")
    elif event.startswith("referral."):
        return notify_referral_users(user_ids, payload, "referral_notification")
    else:
        return notify_generic_users(user_ids, payload, event_type)

def notify_generic_users(user_ids, payload, event_type="notification"):
    channel_layer = get_channel_layer()
    payload = {**payload, "created_at": timezone.now().isoformat()}

    created_notifications = _store_generic_notifications_in_db(user_ids, payload)

    if created_notifications:
        by_user = _group_by_user_id(created_notifications)
        for uid, notes in by_user.items():
            for n in notes:
                data = _serialize_notification(n, include_chat=False, include_referral=True)
                async_to_sync(channel_layer.group_send)(f"notifications_{uid}", {"type": event_type, **data})
    else:
        # Fallback
        for uid in {u for u in user_ids if u}:
            async_to_sync(channel_layer.group_send)(f"notifications_{uid}", {"type": event_type, **payload})

def notify_referral_users(user_ids, payload, event_type="referral_notification"):
    channel_layer = get_channel_layer()
    payload = {**payload, "created_at": timezone.now().isoformat()}

    created_notifications = _store_referral_notifications_in_db(user_ids, payload)

    if created_notifications:
        by_user = _group_by_user_id(created_notifications)
        for uid, notes in by_user.items():
            for n in notes:
                data = _serialize_notification(n, include_chat=False, include_referral=True)
                async_to_sync(channel_layer.group_send)(f"notifications_{uid}", {"type": event_type, **data})
    else:
        for uid in {u for u in user_ids if u}:
            async_to_sync(channel_layer.group_send)(f"notifications_{uid}", {"type": event_type, **payload})

def notify_chat_users(user_ids, payload, event_type="chat_notification"):
    channel_layer = get_channel_layer()
    payload = {**payload, "created_at": timezone.now().isoformat()}

    created_notifications = _store_chat_notifications_in_db(user_ids, payload)

    if created_notifications:
        by_user = _group_by_user_id(created_notifications)
        for uid, notes in by_user.items():
            for n in notes:
                data = _serialize_notification(n, include_chat=True, include_referral=True)
                async_to_sync(channel_layer.group_send)(f"notifications_{uid}", {"type": event_type, **data})
    else:
        for uid in {u for u in user_ids if u}:
            async_to_sync(channel_layer.group_send)(f"notifications_{uid}", {"type": event_type, **payload})

def _store_referral_notifications_in_db(user_ids, payload):
    try:
        from accounts.models import User
        from chat.models import Notification
        from referr.models import Referral

        recipients = User.objects.filter(id__in=user_ids)
        if not recipients.exists():
            return []

        event_type = payload.get("event", "notification")
        title = payload.get("title", "Notification")
        message = payload.get("message", "")
        actors = payload.get("actors", {}) or {}
        meta_data = payload.get("meta", {}) or {}

        referral = None
        referral_id = payload.get("referral_id")
        if referral_id:
            try:
                referral = Referral.objects.get(id=referral_id)
            except Referral.DoesNotExist:
                referral = None

        actor_user = None
        referred_by_id = actors.get("referred_by_id")
        if referred_by_id:
            from accounts.models import User as U
            actor_user = U.objects.filter(id=referred_by_id).first()

        objs = [
            Notification(
                user=r,
                event_type=event_type,
                title=title,
                message=message,
                referral=referral,
                chat_room=None,
                chat_message=None,
                actor_user=actor_user,
                meta_data=meta_data,
            )
            for r in recipients
        ]

        created = _create_notifications_safely(Notification, objs)

        # Pull relateds for serialization
        return Notification.objects.filter(id__in=[o.id for o in created]).select_related(
            "user", "actor_user", "referral"
        )
    except Exception as e:
        print(f"Error storing referral notifications in database: {e}")
        return []

def _store_chat_notifications_in_db(user_ids, payload):
    try:
        from accounts.models import User
        from chat.models import Notification, Message, ChatRoom

        recipients = User.objects.filter(id__in=user_ids)
        if not recipients.exists():
            return []

        event_type = payload.get("event", "notification")
        title = payload.get("title", "Notification")
        message = payload.get("message", "")
        actors = payload.get("actors", {}) or {}
        meta_data = payload.get("meta", {}) or {}

        # Resolve relations
        chat_message = None
        chat_room = None
        actor_user = None

        message_id = payload.get("message_id")
        room_id = payload.get("room_id")

        if message_id:
            chat_message = Message.objects.filter(id=message_id).select_related("chat_room", "sender", "chat_room__referral").first()
            if chat_message:
                chat_room = chat_message.chat_room
                actor_user = chat_message.sender
        elif room_id:
            chat_room = ChatRoom.objects.filter(room_id=room_id).select_related("referral").first()

        if not actor_user:
            sender_id = actors.get("sender_id")
            if sender_id:
                actor_user = User.objects.filter(id=sender_id).first()

        objs = [
            Notification(
                user=r,
                event_type=event_type,
                title=title,
                message=message,
                referral=getattr(chat_room, "referral", None),
                chat_room=chat_room,
                chat_message=chat_message,
                actor_user=actor_user,
                meta_data=meta_data,
            )
            for r in recipients
        ]

        created = _create_notifications_safely(Notification, objs)

        return Notification.objects.filter(id__in=[o.id for o in created]).select_related(
            "user", "actor_user", "referral", "chat_room", "chat_message"
        )
    except Exception as e:
        print(f"Error storing chat notifications in database: {e}")
        return []

def _store_generic_notifications_in_db(user_ids, payload):
    try:
        from accounts.models import User
        from chat.models import Notification
        from referr.models import Referral

        recipients = User.objects.filter(id__in=user_ids)
        if not recipients.exists():
            return []

        event_type = payload.get("event", "notification")
        title = payload.get("title", "Notification")
        message = payload.get("message", "")
        actors = payload.get("actors", {}) or {}
        meta_data = payload.get("meta", {}) or {}

        referral = None
        referral_id = payload.get("referral_id")
        if referral_id:
            referral = Referral.objects.filter(id=referral_id).first()

        actor_user = None
        actor_id = actors.get("actor_id") or actors.get("user_id")
        if actor_id:
            from accounts.models import User as U
            actor_user = U.objects.filter(id=actor_id).first()

        objs = [
            Notification(
                user=r,
                event_type=event_type,
                title=title,
                message=message,
                referral=referral,
                chat_room=None,
                chat_message=None,
                actor_user=actor_user,
                meta_data=meta_data,
            )
            for r in recipients
        ]

        created = _create_notifications_safely(Notification, objs)

        return Notification.objects.filter(id__in=[o.id for o in created]).select_related(
            "user", "actor_user", "referral"
        )
    except Exception as e:
        print(f"Error storing generic notifications in database: {e}")
        return []



def notify_new_message(message, participants_user_ids):
    recipients = [uid for uid in set(participants_user_ids) if uid != message.sender_id]
    if not recipients:
        return

    # Handle different message types
    if message.message_type == 'text':
        snippet = (message.content or "").strip()
        if len(snippet) > 140:
            snippet = snippet[:137] + "…"
    else:
        # For media messages, show a descriptive snippet
        snippet = f"[{message.message_type.upper()}] {message.file_name or 'Media file'}"

    # Get chat room participants for actors
    chat_room = message.chat_room
    participants = chat_room.get_participants()
    
    # Create notification title and message
    notification_title = "New message"
    notification_message = f"{message.sender.full_name} sent a message: {snippet}"
    payload = {
        "event": "chat.new_message",
        "message_id": message.id,
        "room_id": chat_room.room_id,
        "title": notification_title,
        "message": notification_message,
        "actors": {
            "sender_id": message.sender_id,
            "solo_user_id": chat_room.solo_user.id if chat_room.solo_user else None,
            "company_user_id": chat_room.company_user.id if chat_room.company_user else None,
            "rep_user_id": chat_room.rep_user.id if chat_room.rep_user else None,
        },
        "meta": {
            "sender_name": message.sender.full_name,
            "room_type": chat_room.room_type,
            "message_type": message.message_type,
            "text_snippet": snippet,
            "referral_id": chat_room.referral.reference_id if chat_room.referral else None,
            "created_at_ts": int(message.created_at.timestamp()),
        }
    }
    
    # Send using chat-specific notify function (which now also stores in DB)
    notify_chat_users(recipients, payload, "new_message_notification")




# {
#   "actor_user": {
#     "full_name": "Fawad Worker",
#     "id": 16
#   },
#   "chat_message": {
#     "content": "uii",
#     "id": 176,
#     "message_type": "text"
#   },
#   "chat_room": {
#     "id": 1,
#     "room_id": "rep_16_solo_15_ref_5",
#     "room_type": "rep_solo"
#   },
#   "created_at": "2025-10-13T17:19:53.735334+00:00",
#   "event_type": "chat.new_message",
#   "id": null,
#   "is_read": false,
#   "message": "Fawad Worker sent a message: uii",
#   "meta_data": {
#     "created_at_ts": 1760375993,
#     "message_type": "text",
#     "referral_id": "REF-439D7C93",
#     "room_type": "rep_solo",
#     "sender_name": "Fawad Worker",
#     "text_snippet": "uii"
#   },
#   "referral": {
#     "id": 5,
#     "reference_id": "REF-439D7C93",
#     "service_type": "",
#     "status": "Friend opted in"
#   },
#   "title": "New message",
#   "type": "new_message_notification"
# }



