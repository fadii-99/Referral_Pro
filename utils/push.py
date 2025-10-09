from django.conf import settings
import os
import firebase_admin
from firebase_admin import credentials, messaging
from accounts.models import Device

def initialize_firebase():
    """Initialize Firebase Admin SDK with service account"""
    service_account_path = os.path.join(settings.BASE_DIR, "firebase_service_account.json")

    if not os.path.exists(service_account_path):
        print(f"⚠️  Firebase service account not found at {service_account_path}")
        return None

    try:
        if not firebase_admin._apps:  # prevents duplicate initialization
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin initialized successfully")
        return messaging
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return None

# Initialize once globally
firebase_messaging = initialize_firebase()

def send_push_notification_to_user(user, title, body, data=None):
    """Send notification only to offline devices of a user"""
    try:
        if firebase_messaging is None:
            print("Firebase not initialized. Cannot send notification.")
            return {"error": "Firebase not initialized"}

        print(f"\n\n Preparing to send push notification to user {user.id}")
        
        # Get only OFFLINE devices for the user to prevent duplicate notifications
        offline_devices = Device.objects.filter(user=user, is_online=False)
        
        if not offline_devices.exists():
            print(f"⚠️  User {user.id} has no offline devices - skipping push notification")
            return {"info": "User has no offline devices", "success": 0, "failure": 0}

        print(f"User {user.id} has {offline_devices.count()} offline devices")

        # Send to each offline device individually
        successful_sends = []
        failed_sends = []
        invalid_tokens = []
        
        for device in offline_devices:
            token = device.token
            if not token:
                print(f"⚠️  No FCM token for offline device {device.id} of user {user.id}")
                continue
                
            try:
                message = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data={k: str(v) for k, v in (data or {}).items()},  # Convert all values to strings
                    token=token,
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            sound="default",
                            channel_id="default"  # You can customize this
                        )
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                sound="default",
                                badge=1  # You can customize this
                            )
                        )
                    )
                )
                
                # Send individual message
                message_id = firebase_messaging.send(message)
                successful_sends.append(message_id)
                print(f"✅ Sent to offline device {device.id} token {token[:10]}... - Message ID: {message_id}")
                
            except Exception as send_error:
                failed_sends.append(token)
                error_str = str(send_error)
                print(f"❌ Failed to send to offline device {device.id} token {token[:10]}... - Error: {error_str}")

                # Check if token is invalid and should be removed
                if any(err_code in error_str.lower() for err_code in [
                    "registration-token-not-registered", 
                    "invalid-argument",
                    "sender-id-mismatch",
                    "invalid registration token"
                ]):
                    invalid_tokens.append(token)
                    print(f"🗑️ Marking token {token[:10]}... for removal")

        # Clean up invalid tokens from database
        if invalid_tokens:
            Device.objects.filter(user=user, token__in=invalid_tokens).delete()
            print(f"🧹 Removed {len(invalid_tokens)} invalid tokens for user {user.id}")

        success_count = len(successful_sends)
        failure_count = len(failed_sends)
        
        print(f"✅ Push notification sent to offline devices: {success_count} successful, {failure_count} failed for user {user.id}")

        return {
            "success": success_count,
            "failure": failure_count,
            "total_sent": offline_devices.count(),
            "invalid_tokens": invalid_tokens,
            "message_ids": successful_sends
        }

    except Exception as e:
        print(f"❌ Error sending notification to user {user.id}: {e}")
        return {"error": str(e)}

# def send_push_notification_to_multiple_users(users, title, body, data=None):
#     """Send notification to multiple users"""
#     if firebase_messaging is None:
#         print("Firebase not initialized. Cannot send notifications.")
#         return {"error": "Firebase not initialized"}
        
#     results = {}
#     print(f"Sending notifications to {len(users)} users")
    
#     for user in users:
#         try:
#             result = send_push_notification_to_user(user, title, body, data)
#             results[user.id] = result
#         except Exception as e:
#             results[user.id] = {"error": str(e)}
#             print(f"❌ Failed to send to user {user.id}: {e}")
    
#     return results

# def send_push_notification_to_topic(topic, title, body, data=None):
#     """Send notification to a topic (for group notifications)"""
#     try:
#         if firebase_messaging is None:
#             return {"error": "Firebase not initialized"}

#         message = messaging.Message(
#             notification=messaging.Notification(title=title, body=body),
#             data={k: str(v) for k, v in (data or {}).items()},
#             topic=topic,
#             android=messaging.AndroidConfig(priority="high"),
#             apns=messaging.APNSConfig(payload=messaging.APNSPayload(
#                 aps=messaging.Aps(sound="default")
#             ))
#         )

#         message_id = firebase_messaging.send(message)
#         print(f"✅ Topic notification sent: {message_id}")
        
#         return {"success": True, "message_id": message_id}

#     except Exception as e:
#         print(f"❌ Error sending topic notification: {e}")
#         return {"error": str(e)}

# # Legacy function for backward compatibility
# # def send_push_notification_to_single_user(user, title, body, data=None):
# #     """Send push notification to a single user (legacy method)"""
# #     return send_push_notification_to_user(user, title, body, data)

# # Utility functions for token management
# def subscribe_user_to_topic(user, topic):
#     """Subscribe user's devices to a topic"""
#     try:
#         if firebase_messaging is None:
#             return {"error": "Firebase not initialized"}

#         tokens = list(user.devices.values_list("token", flat=True))
#         if not tokens:
#             return {"error": "No tokens for user"}

#         response = firebase_messaging.subscribe_to_topic(tokens, topic)
#         print(f"✅ Subscribed user {user.id} to topic '{topic}': {response.success_count} successful")
        
#         return {
#             "success": response.success_count,
#             "failure": response.failure_count
#         }

#     except Exception as e:
#         print(f"❌ Error subscribing user {user.id} to topic '{topic}': {e}")
#         return {"error": str(e)}

# def unsubscribe_user_from_topic(user, topic):
#     """Unsubscribe user's devices from a topic"""
#     try:
#         if firebase_messaging is None:
#             return {"error": "Firebase not initialized"}

#         tokens = list(user.devices.values_list("token", flat=True))
#         if not tokens:
#             return {"error": "No tokens for user"}

#         response = firebase_messaging.unsubscribe_from_topic(tokens, topic)
#         print(f"✅ Unsubscribed user {user.id} from topic '{topic}': {response.success_count} successful")
        
#         return {
#             "success": response.success_count,
#             "failure": response.failure_count
#         }

#     except Exception as e:
#         print(f"❌ Error unsubscribing user {user.id} from topic '{topic}': {e}")
#         return {"error": str(e)}
