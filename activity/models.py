# activity/models.py
from django.db import models
from django.utils import timezone
from accounts.models import User
from referr.models import Referral
from chat.models import ChatRoom, Message

class ActivityLog(models.Model):
    class Event(models.TextChoices):
        SEND_REFERRAL      = "send_referral", "Send Referral"
        FRIEND_OPTIN       = "friend_optin", "Friend Opt-in"
        FRIEND_ACCEPTED    = "friend_accepted", "Friend Accepted"
        REP_ASSIGNED       = "rep_assigned", "Rep Assigned"
        CHATTING           = "chatting", "Chatting"
        COMPLETED          = "completed", "Completed"
        CANCELLED          = "cancelled", "Cancelled"

    event = models.CharField(max_length=40, choices=Event.choices)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_actor")
    referral = models.ForeignKey(Referral, null=True, blank=True, on_delete=models.SET_NULL, related_name="activities")
    chat_room = models.ForeignKey(ChatRoom, null=True, blank=True, on_delete=models.SET_NULL, related_name="activities")
    message = models.ForeignKey(Message, null=True, blank=True, on_delete=models.SET_NULL, related_name="activities")

    # Optional second user (e.g., the rep that got assigned, the friend who opted, etc.)
    subject_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_subject")

    # Freeform text + structured metadata
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)

    # Use the generic JSONField that works with MySQL, PostgreSQL, SQLite, etc.
    meta = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["referral", "created_at"]),
            models.Index(fields=["event", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        rid = getattr(self.referral, "reference_id", None)
        return f"{self.event} | ref={rid} | at={self.created_at.isoformat()}"
