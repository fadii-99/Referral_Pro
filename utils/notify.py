# utils/notify.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

def notify_users(user_ids, payload, event_type="notification"):
    """Generic notification dispatcher - routes to specific handlers"""
    event = payload.get('event', '')
    
    if event.startswith('chat.'):
        # Route to chat notification handler -> send consumer handler name
        return notify_chat_users(user_ids, payload, "new_message_notification")
    elif event.startswith('referral.'):
        # Route to referral notification handler  
        return notify_referral_users(user_ids, payload, "referral_notification")
    else:
        # Default fallback for other notification types
        return notify_generic_users(user_ids, payload, event_type)

def notify_generic_users(user_ids, payload, event_type="notification"):
    """Handle generic notifications (fallback)"""
    channel_layer = get_channel_layer()
    payload = {**payload, "created_at": timezone.now().isoformat()}
    
    # Store notifications in database and get the created notifications
    created_notifications = _store_generic_notifications_in_db(user_ids, payload)
    
    # Send real-time notifications via WebSocket using DB notification data
    if created_notifications:
        # Group notifications by user_id for efficient sending
        notifications_by_user = {}
        for notification in created_notifications:
            user_id = notification.user_id
            if user_id not in notifications_by_user:
                notifications_by_user[user_id] = []
            
            # Convert notification to JSON format (same as API)
            notification_data = {
                "id": notification.id,
                "event_type": notification.event_type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
                "meta_data": notification.meta_data,
                "actor_user": {
                    "id": notification.actor_user.id,
                    "full_name": notification.actor_user.full_name,
                    # "avatar_url": notification.actor_user.image.url if notification.actor_user.image else None
                } if notification.actor_user else None,
                "referral": {
                    "id": notification.referral.id,
                    "reference_id": notification.referral.reference_id,
                    "service_type": notification.referral.service_type,
                    "status": notification.referral.status
                } if notification.referral else None,
                "chat_room": {
                    "id": notification.chat_room.id,
                    "room_id": notification.chat_room.room_id,
                    "room_type": notification.chat_room.room_type
                } if notification.chat_room else None
            }
            notifications_by_user[user_id].append(notification_data)
        
        # Send WebSocket notifications with updated payload
        for user_id, user_notifications in notifications_by_user.items():
            for notification_data in user_notifications:
                async_to_sync(channel_layer.group_send)(
                    f"notifications_{user_id}",
                    {"type": event_type, **notification_data},
                )
    else:
        # Fallback to original method if DB storage fails
        for uid in {u for u in user_ids if u}:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{uid}",
                {"type": event_type, **payload},
            )

def notify_referral_users(user_ids, payload, event_type="referral_notification"):
    """Handle referral-specific notifications"""
    channel_layer = get_channel_layer()
    payload = {**payload, "created_at": timezone.now().isoformat()}
    
    # Store notifications in database and get the created notifications
    created_notifications = _store_referral_notifications_in_db(user_ids, payload)
    
    # Send real-time notifications via WebSocket using DB notification data
    if created_notifications:
        # Group notifications by user_id for efficient sending
        notifications_by_user = {}
        for notification in created_notifications:
            user_id = notification.user_id
            if user_id not in notifications_by_user:
                notifications_by_user[user_id] = []
            
            # Convert notification to JSON format (same as API) for referral
            notification_data = {
                "id": notification.id,
                "event_type": notification.event_type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
                "meta_data": notification.meta_data,
                "actor_user": {
                    "id": notification.actor_user.id,
                    "full_name": notification.actor_user.full_name,
                    # "avatar_url": notification.actor_user.image.url if notification.actor_user.image else None
                } if notification.actor_user else None,
                "referral": {
                    "id": notification.referral.id,
                    "reference_id": notification.referral.reference_id,
                    "service_type": notification.referral.service_type,
                    "status": notification.referral.status
                } if notification.referral else None,
                "chat_room": None
            }
            notifications_by_user[user_id].append(notification_data)
        
        # Send WebSocket notifications with updated payload
        for user_id, user_notifications in notifications_by_user.items():
            for notification_data in user_notifications:
                async_to_sync(channel_layer.group_send)(
                    f"notifications_{user_id}",
                    {"type": event_type, **notification_data},
                )
    else:
        # Fallback to original method if DB storage fails
        for uid in {u for u in user_ids if u}:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{uid}",
                {"type": event_type, **payload},
            )

def notify_chat_users(user_ids, payload, event_type="chat_notification"):
    """Handle chat-specific notifications"""
    # change default event_type to match consumer handler name
    channel_layer = get_channel_layer()
    payload = {**payload, "created_at": timezone.now().isoformat()}
    
    # Store notifications in database and get the created notifications
    created_notifications = _store_chat_notifications_in_db(user_ids, payload)
    
    # Send real-time notifications via WebSocket using DB notification data
    if created_notifications:
        # Group notifications by user_id for efficient sending
        notifications_by_user = {}
        for notification in created_notifications:
            user_id = notification.user_id
            if user_id not in notifications_by_user:
                notifications_by_user[user_id] = []
            
            # Convert notification to JSON format (same as API) for chat
            notification_data = {
                "id": notification.id,
                "event_type": notification.event_type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
                "meta_data": notification.meta_data,
                "actor_user": {
                    "id": notification.actor_user.id,
                    "full_name": notification.actor_user.full_name,
                    # "avatar_url": notification.actor_user.image.url if notification.actor_user.image else None
                } if notification.actor_user else None,
                "referral": {
                    "id": notification.referral.id,
                    "reference_id": notification.referral.reference_id,
                    "service_type": notification.referral.service_type,
                    "status": notification.referral.status
                } if notification.referral else None,
                "chat_room": {
                    "id": notification.chat_room.id,
                    "room_id": notification.chat_room.room_id,
                    "room_type": notification.chat_room.room_type
                } if notification.chat_room else None,
                "chat_message": {
                    "id": notification.chat_message.id,
                    "message_type": notification.chat_message.message_type,
                    "content": notification.chat_message.content if notification.chat_message.message_type == 'text' else f"[{notification.chat_message.message_type.upper()}]"
                } if notification.chat_message else None
            }
            notifications_by_user[user_id].append(notification_data)
        
        # Send WebSocket notifications with updated payload
        for user_id, user_notifications in notifications_by_user.items():
            for notification_data in user_notifications:
                async_to_sync(channel_layer.group_send)(
                    f"notifications_{user_id}",
                    {"type": event_type, **notification_data},
                )
    else:
        # Fallback to original method if DB storage fails
        for uid in {u for u in user_ids if u}:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{uid}",
                {"type": event_type, **payload},
            )

def _store_referral_notifications_in_db(user_ids, payload):
    """Store referral notifications in database for persistence"""
    try:
        from accounts.models import User
        from chat.models import Notification
        from referr.models import Referral
        
        # Get recipient users
        recipient_users = User.objects.filter(id__in=user_ids)
        if not recipient_users.exists():
            return []
        
        notifications_to_create = []
        event_type = payload.get('event', 'notification')
        
        # Extract common fields
        title = payload.get('title', 'Notification')
        message = payload.get('message', '')
        actors = payload.get('actors', {})
        meta_data = payload.get('meta', {})
        
        # Get related objects for referral notifications
        referral = None
        actor_user = None
        
        # For referral notifications
        referral_id = payload.get('referral_id')
        if referral_id:
            try:
                referral = Referral.objects.get(id=referral_id)
            except Referral.DoesNotExist:
                pass
        
        # Get actor user (the one who sent the referral)
        referred_by_id = actors.get('referred_by_id')
        if referred_by_id:
            try:
                actor_user = User.objects.get(id=referred_by_id)
            except User.DoesNotExist:
                pass
        
        # Create notification records for each recipient
        for recipient in recipient_users:
            notifications_to_create.append(
                Notification(
                    user=recipient,
                    event_type=event_type,
                    title=title,
                    message=message,
                    referral=referral,
                    chat_room=None,
                    chat_message=None,
                    actor_user=actor_user,
                    meta_data=meta_data
                )
            )
        
        # Bulk create notification records
        if notifications_to_create:
            created_notifications = Notification.objects.bulk_create(notifications_to_create)
            print(f"Created {len(created_notifications)} referral notification records for event: {event_type}")
            
            # If bulk_create doesn't return objects with IDs, fetch them
            if not created_notifications or not hasattr(created_notifications[0], 'id'):
                # Get the notifications we just created
                created_notifications = Notification.objects.filter(
                    user__in=recipient_users,
                    event_type=event_type,
                    created_at__gte=timezone.now() - timezone.timedelta(seconds=5)
                ).select_related('user', 'actor_user', 'referral')
            
            return created_notifications
        
        return []
            
    except Exception as e:
        print(f"Error storing referral notifications in database: {str(e)}")
        return []

def _store_chat_notifications_in_db(user_ids, payload):
    """Store chat notifications in database for persistence"""
    try:
        from accounts.models import User
        from chat.models import Notification, Message, ChatRoom
        from referr.models import Referral
        
        # Get recipient users
        recipient_users = User.objects.filter(id__in=user_ids)
        if not recipient_users.exists():
            return []
        
        notifications_to_create = []
        event_type = payload.get('event', 'notification')
        
        # Extract common fields
        title = payload.get('title', 'Notification')
        message = payload.get('message', '')
        actors = payload.get('actors', {})
        meta_data = payload.get('meta', {})
        
        # Get related objects for chat notifications
        referral = None
        chat_room = None
        chat_message = None
        actor_user = None
        
        # For chat notifications
        message_id = payload.get('message_id')
        room_id = payload.get('room_id')
        
        if message_id:
            try:
                chat_message = Message.objects.get(id=message_id)
                chat_room = chat_message.chat_room
                referral = chat_room.referral
                actor_user = chat_message.sender
            except Message.DoesNotExist:
                pass
        elif room_id:
            try:
                chat_room = ChatRoom.objects.get(room_id=room_id)
                referral = chat_room.referral
            except ChatRoom.DoesNotExist:
                pass
        
        # Get sender as actor if available
        sender_id = actors.get('sender_id')
        if sender_id and not actor_user:
            try:
                actor_user = User.objects.get(id=sender_id)
            except User.DoesNotExist:
                pass
        
        # Create notification records for each recipient
        for recipient in recipient_users:
            notifications_to_create.append(
                Notification(
                    user=recipient,
                    event_type=event_type,
                    title=title,
                    message=message,
                    referral=referral,
                    chat_room=chat_room,
                    chat_message=chat_message,
                    actor_user=actor_user,
                    meta_data=meta_data
                )
            )
        
        # Bulk create notification records
        if notifications_to_create:
            created_notifications = Notification.objects.bulk_create(notifications_to_create)
            print(f"Created {len(created_notifications)} chat notification records for event: {event_type}")
            
            # If bulk_create doesn't return objects with IDs, fetch them
            if not created_notifications or not hasattr(created_notifications[0], 'id'):
                # Get the notifications we just created
                created_notifications = Notification.objects.filter(
                    user__in=recipient_users,
                    event_type=event_type,
                    created_at__gte=timezone.now() - timezone.timedelta(seconds=5)
                ).select_related('user', 'actor_user', 'referral', 'chat_room', 'chat_message')
            
            return created_notifications
        
        return []
            
    except Exception as e:
        print(f"Error storing chat notifications in database: {str(e)}")
        return []

def _store_generic_notifications_in_db(user_ids, payload):
    """Store generic notifications in database for persistence"""
    try:
        from accounts.models import User
        from chat.models import Notification
        from referr.models import Referral
        
        # Get recipient users
        recipient_users = User.objects.filter(id__in=user_ids)
        if not recipient_users.exists():
            return []
        
        notifications_to_create = []
        event_type = payload.get('event', 'notification')
        
        # Extract common fields
        title = payload.get('title', 'Notification')
        message = payload.get('message', '')
        actors = payload.get('actors', {})
        meta_data = payload.get('meta', {})
        
        # Get related objects based on event type
        referral = None
        actor_user = None
        
        # For generic notifications, try to get basic relations
        referral_id = payload.get('referral_id')
        if referral_id:
            try:
                referral = Referral.objects.get(id=referral_id)
            except Referral.DoesNotExist:
                pass
        
        # Get actor user if available
        actor_id = actors.get('actor_id') or actors.get('user_id')
        if actor_id:
            try:
                actor_user = User.objects.get(id=actor_id)
            except User.DoesNotExist:
                pass
        
        # Create notification records for each recipient
        for recipient in recipient_users:
            notifications_to_create.append(
                Notification(
                    user=recipient,
                    event_type=event_type,
                    title=title,
                    message=message,
                    referral=referral,
                    chat_room=None,
                    chat_message=None,
                    actor_user=actor_user,
                    meta_data=meta_data
                )
            )
        
        # Bulk create notification records
        if notifications_to_create:
            created_notifications = Notification.objects.bulk_create(notifications_to_create)
            print(f"Created {len(created_notifications)} generic notification records for event: {event_type}")
            
            # If bulk_create doesn't return objects with IDs, fetch them
            if not created_notifications or not hasattr(created_notifications[0], 'id'):
                # Get the notifications we just created
                created_notifications = Notification.objects.filter(
                    user__in=recipient_users,
                    event_type=event_type,
                    created_at__gte=timezone.now() - timezone.timedelta(seconds=5)
                ).select_related('user', 'actor_user', 'referral')
            
            return created_notifications
        
        return []
            
    except Exception as e:
        print(f"Error storing generic notifications in database: {str(e)}")
        return []



def notify_new_message(message, participants_user_ids):
    print("Notifying users of new message...")
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
    
    print(f"Notification payload: {payload}")
    # Send using chat-specific notify function (which now also stores in DB)
    notify_chat_users(recipients, payload, "new_message_notification")
