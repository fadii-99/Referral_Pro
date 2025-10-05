# utils/notify.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

def notify_users(user_ids, payload, event_type="referral_notification"):
    channel_layer = get_channel_layer()
    payload = {**payload, "created_at": timezone.now().isoformat()}
    for uid in {u for u in user_ids if u}:
        async_to_sync(channel_layer.group_send)(
            f"notifications_{uid}",
            {"type": event_type, **payload},
        )

def notify_new_message(message, participants_user_ids):
    recipients = [uid for uid in set(participants_user_ids) if uid != message.sender_id]
    if not recipients:
        return

    snippet = (message.text or "").strip()
    if len(snippet) > 140:
        snippet = snippet[:137] + "…"

    payload = {
        "event": "chat.new_message",
        "room_id": message.room_id,
        "message_id": message.id,
        "sender_id": message.sender_id,
        "sender_name": getattr(message.sender, "full_name", None) or getattr(message.sender, "username", "Someone"),
        "text_snippet": snippet,
        "created_at_ts": int(message.created_at.timestamp()),
    }
    # Send using a separate consumer handler name to keep it clean
    notify_users(recipients, payload, event_type="new_message_notification")
