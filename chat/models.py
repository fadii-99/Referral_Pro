from django.db import models
from django.utils import timezone
from accounts.models import User
from referr.models import Referral


class ChatRoom(models.Model):
    """
    Chat room model that handles different types of conversations:
    1. Rep-Solo chat (assigned rep chats with referred solo)
    2. Company-Solo chat (when biz_type='individual', company directly chats with solo)
    """
    ROOM_TYPES = [
        ('rep_solo', 'Rep to Solo'),
        ('company_solo', 'Company to Solo'),
    ]
    
    room_id = models.CharField(max_length=100, unique=True)
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='chat_rooms')
    room_type = models.CharField(max_length=20, null=True, blank=True)
    
    # Participants
    solo_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='solo_chat_rooms',
        limit_choices_to={'role': 'solo'}
    )
    rep_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='rep_chat_rooms',
        null=True, 
        blank=True,
        limit_choices_to={'role': 'rep'}
    )
    company_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='company_chat_rooms',
        limit_choices_to={'role': 'company'}
    )
    
    # Room status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Last activity tracking
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['referral', 'solo_user', 'company_user']
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.room_type == 'rep_solo':
            return f"Chat: {self.rep_user.full_name} (Rep) ↔ {self.solo_user.full_name} (Solo) | Ref: {self.referral.reference_id}"
        else:
            return f"Chat: {self.company_user.full_name} (Company) ↔ {self.solo_user.full_name} (Solo) | Ref: {self.referral.reference_id}"
    
    def can_user_participate(self, user):
        """Check if a user can participate in this chat room"""
        if user == self.solo_user:
            print("Solo user can participate")
            return True
        if user == self.company_user:
            print("Company user can participate")
            return True
        if user == self.rep_user:
            print("Rep user can participate")
            return True
        
        # Company can oversee their reps' conversations
        # if user.role == 'company' and self.rep_user and self.rep_user.parent_company == user:
        #     return True
        print("User cannot participate")
            
        return False
    
    def get_participants(self):
        """Get all users who can participate in this room"""
        participants = [self.solo_user, self.company_user]
        if self.rep_user:
            participants.append(self.rep_user)
        return participants
    
    def get_display_name(self, viewer):
        """Get display name based on viewer's role"""
        if viewer == self.solo_user:
            if hasattr(self.company_user, "business_info"):
                return self.company_user.business_info.company_name
            return self.company_user.full_name
        elif viewer == self.rep_user or viewer == self.company_user:
            # Rep or company sees solo user name
            return self.solo_user.full_name
        else:
            return "Unknown"
    
    def get_chat_image(self, viewer):
        """Get chat image based on viewer's role"""
        if viewer == self.solo_user:
            # Solo user sees company's image
            return self.company_user.get_image_url()
        elif viewer == self.rep_user or viewer == self.company_user:

            # Rep or company sees solo user's image
            return self.solo_user.get_image_url()
        else:
            return None
    
    def get_last_message_summary(self):
        """Get summary of the last message in this room"""
        last_message = self.messages.select_related('sender').last()
        if not last_message:
            return {
                "content": "No messages yet",
                "sender_name": "",
                "timestamp": None,
                "message_type": "system"
            }
        
        # Format content based on message type
        if last_message.message_type == 'text':
            content = last_message.content[:100] + ('...' if len(last_message.content) > 100 else '')
        else:
            content = f"[{last_message.message_type.upper()}] {last_message.file_name or 'Media file'}"
        
        return {
            "content": content,
            "sender_name": last_message.sender.full_name,
            "timestamp": last_message.created_at.isoformat(),
            "message_type": last_message.message_type,
            "sender_id": last_message.sender.id
        }
    
    def get_unread_count(self, user):
        """Get count of unread messages for a specific user"""
        from django.db.models import Count, Q
        
        # Count messages that don't have a read status for this user
        unread_count = self.messages.exclude(
            read_statuses__user=user
        ).exclude(
            sender=user  # Don't count user's own messages as unread
        ).count()
        
        return unread_count
    
    def is_any_participant_online(self, exclude_user=None):
        """Check if any participant (except excluded user) is online"""
        participants = self.participants.filter(is_online=True)
        
        if exclude_user:
            participants = participants.exclude(user=exclude_user)
        
        return participants.exists()
    
    @classmethod
    def create_room_for_referral(cls, referral, solo_user, assigned_rep=None):
        company_user = referral.company
        
        if hasattr(company_user, 'business_info') and company_user.business_info.biz_type == 'individual':
            room_type = 'company_solo'
            room_id = f"company_{company_user.id}_solo_{solo_user.id}_ref_{referral.id}"
            rep_user = None
        else:
            if not assigned_rep:
                raise ValueError("Rep is required for non-individual business type")
            room_type = 'rep_solo'
            room_id = f"rep_{assigned_rep.id}_solo_{solo_user.id}_ref_{referral.id}"
            rep_user = assigned_rep
        
        existing_room = cls.objects.filter(
            referral=referral,
            solo_user=solo_user,
            company_user=company_user,
            rep_user=rep_user
        ).first()
        
        if existing_room:
            return existing_room
        
        return cls.objects.create(
            room_id=room_id,
            room_type=room_type,
            referral=referral,
            solo_user=solo_user,
            rep_user=rep_user,
            company_user=company_user
        )



class Message(models.Model):
    """
    Message model for chat conversations with comprehensive media support
    """
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio/Voice'),
        ('document', 'Document'),
        ('file', 'File'),
        ('system', 'System Message'),
    ]
    
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True)  # Optional for media messages
    
    # File attachments with comprehensive support - store path like user profile images
    from utils.storage_backends import MediaStorage
    media_storage = MediaStorage()
    
    attachment = models.FileField(upload_to="chat_files/", storage=media_storage, null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)  # Size in bytes
    file_type = models.CharField(max_length=100, blank=True, null=True)  # MIME type
    
    # Media-specific metadata
    duration = models.PositiveIntegerField(blank=True, null=True)  # For audio/video (seconds)
    thumbnail_url = models.URLField(blank=True, null=True)  # For videos/images
    dimensions = models.JSONField(blank=True, null=True)  # {"width": 1920, "height": 1080}
    
    # Message status
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Reply/Thread support
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat_room', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['message_type']),
        ]
    
    def __str__(self):
        if self.message_type == 'text':
            return f"{self.sender.full_name}: {self.content[:50]}..." if len(self.content) > 50 else f"{self.sender.full_name}: {self.content}"
        else:
            return f"{self.sender.full_name}: [{self.message_type.upper()}] {self.file_name or 'Media file'}"
    
    def save(self, *args, **kwargs):
        """Update chat room's last message timestamp and broadcast updates"""
        super().save(*args, **kwargs)
        self.chat_room.last_message_at = self.created_at
        self.chat_room.save(update_fields=['last_message_at', 'updated_at'])
        
        # Send real-time updates to WebSocket consumers
        self._send_realtime_updates()
    
    def _send_realtime_updates(self):
        """Send real-time updates to chat and chat-list consumers"""
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            from .serializers import MessageSerializer, ChatRoomListSerializer
            
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
            
            # Create a proper mock request object
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                    self.META = {'HTTP_HOST': 'localhost', 'wsgi.url_scheme': 'http'}
                
                def build_absolute_uri(self, location=None):
                    if location:
                        return f"http://localhost{location}"
                    return "http://localhost/"
            
            # Send message to chat room (without request context to avoid serializer issues)
            message_data = {
                "id": self.id,
                "content": self.content,
                "sender_id": self.sender.id,
                "sender_name": getattr(self.sender, 'full_name', str(self.sender)),
                "sender_role": getattr(self.sender, 'role', ''),
                "message_type": self.message_type,
                "timestamp": self.created_at.isoformat(),
                "file_url": self.get_file_url(),  # Use the method to get presigned URL
                "file_name": self.file_name,
                "file_size": self.file_size,
                "file_type": self.file_type,
                "duration": self.duration,
                "thumbnail_url": self.thumbnail_url,
                "dimensions": self.dimensions,
            }
            
            async_to_sync(channel_layer.group_send)(
                f"chat_{self.chat_room.room_id}",
                {
                    "type": "chat_message",
                    "message": message_data
                }
            )
            
            # Send chat list updates to all participants
            participants = self.chat_room.get_participants()
            for participant in participants:
                # Get updated chat rooms for this participant
                from django.db.models import Q, Count
                if participant.role == 'solo':
                    chat_rooms = ChatRoom.objects.filter(solo_user=participant)
                elif participant.role in ['rep', 'employee']:
                    chat_rooms = ChatRoom.objects.filter(rep_user=participant)
                elif participant.role == 'company':
                    chat_rooms = ChatRoom.objects.filter(
                        Q(company_user=participant) | 
                        Q(rep_user__parent_company=participant)
                    )
                else:
                    continue
                
                chat_rooms = chat_rooms.annotate(
                    unread_count=Count(
                        'messages', 
                        filter=~Q(messages__read_statuses__user=participant)
                    )
                ).select_related(
                    'solo_user', 'rep_user', 'company_user', 'referral'
                ).prefetch_related(
                    'messages'
                ).order_by('-last_message_at')
                
                # Create serialized data manually to avoid request context issues
                chat_list_data = []
                for room in chat_rooms:
                    chat_list_data.append({
                        "room_id": room.room_id,
                        "room_type": room.room_type,
                        "name": room.get_display_name(participant),
                        "last_message": room.get_last_message_summary(),
                        "unread_count": room.get_unread_count(participant),
                        "is_online": room.is_any_participant_online(exclude_user=participant),
                        "is_active": room.is_active,
                        "created_at": room.created_at.isoformat(),
                        "updated_at": room.updated_at.isoformat(),
                        "referral_id": room.referral.reference_id if room.referral else None,
                    })
                
                async_to_sync(channel_layer.group_send)(
                    f"chat_list_{participant.id}",
                    {
                        "type": "chat_list_update",
                        "chat_rooms": chat_list_data
                    }
                )
                
        except Exception as e:
            print(f"Error sending real-time updates: {e}")
    
    @property
    def is_media(self):
        """Check if message contains media"""
        return self.message_type in ['image', 'video', 'audio', 'document', 'file']
    
    @property
    def file_size_formatted(self):
        size = self.file_size
        if size is None: 
            return None
        for unit in ['B','KB','MB','GB','TB']:
            if size < 1024.0 or unit == 'TB':
                return f"{size:.1f} {unit}"
            size /= 1024.0
    
    def get_file_url(self):
        """Get the presigned URL for the attachment file"""
        if self.attachment:
            from utils.storage_backends import generate_presigned_url
            return generate_presigned_url(f"media/{self.attachment}", expires_in=3600)
        return None
    
    def get_attachments_data(self):
        """Get all attachments data for this message"""
        attachments = []
        
        # Add primary attachment if exists
        if self.attachment:
            attachments.append({
                'file_url': self.get_file_url(),
                'file_name': self.file_name,
                'file_size': self.file_size,
                'file_type': self.file_type,
                'file_size_formatted': self.file_size_formatted
            })
        
        # Add additional attachments
        for attachment in self.additional_attachments.all():
            attachments.append({
                'file_url': attachment.get_file_url(),
                'file_name': attachment.file_name,
                'file_size': attachment.file_size,
                'file_type': attachment.file_type,
                'file_size_formatted': attachment.file_size_formatted
            })
            
        return attachments


class MessageAttachment(models.Model):
    """
    Model for multiple file attachments per message
    """
    from utils.storage_backends import MediaStorage
    media_storage = MediaStorage()
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='additional_attachments')
    attachment = models.FileField(upload_to="chat_files/", storage=media_storage)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=100)  # MIME type
    
    # Media-specific metadata
    duration = models.PositiveIntegerField(blank=True, null=True)  # For audio/video (seconds)
    thumbnail_url = models.URLField(blank=True, null=True)  # For videos/images
    dimensions = models.JSONField(blank=True, null=True)  # {"width": 1920, "height": 1080}
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"Attachment: {self.file_name} for message {self.message.id}"
    
    def get_file_url(self):
        """Get the presigned URL for the attachment file"""
        if self.attachment:
            from utils.storage_backends import generate_presigned_url
            return generate_presigned_url(f"media/{self.attachment}", expires_in=3600)
        return None
    
    @property
    def file_size_formatted(self):
        size = self.file_size
        if size is None: 
            return None
        for unit in ['B','KB','MB','GB','TB']:
            if size < 1024.0 or unit == 'TB':
                return f"{size:.1f} {unit}"
            size /= 1024.0


class MessageReadStatus(models.Model):
    """
    Track read status of messages for each user
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reads')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
        ordering = ['-read_at']
    
    def __str__(self):
        return f"{self.user.full_name} read message at {self.read_at}"


class ChatParticipant(models.Model):
    """
    Track active participants in chat rooms with their roles and permissions
    """
    PARTICIPANT_ROLES = [
        ('primary', 'Primary Participant'),  # Solo, Rep, or Company (direct participant)
        ('observer', 'Observer'),  # Company observing rep's conversation
    ]
    
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_participations')
    role = models.CharField(max_length=10, choices=PARTICIPANT_ROLES, default='primary')
    
    # Permissions
    can_send_messages = models.BooleanField(default=True)
    can_view_history = models.BooleanField(default=True)
    
    # Activity tracking
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['chat_room', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.full_name} in {self.chat_room.room_id} ({self.role})"
