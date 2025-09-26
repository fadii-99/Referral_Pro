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
            return True
        if user == self.company_user:
            return True
        if self.rep_user and user == self.rep_user:
            return True
        
        # Company can oversee their reps' conversations
        if user.role == 'company' and self.rep_user and self.rep_user.parent_company == user:
            return True
            
        return False
    
    def get_participants(self):
        """Get all users who can participate in this room"""
        participants = [self.solo_user, self.company_user]
        if self.rep_user:
            participants.append(self.rep_user)
        return participants
    
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
    Message model for chat conversations
    """
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System Message'),
    ]
    
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    
    # File attachments
    file_url = models.URLField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    
    # Message status
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.full_name}: {self.content[:50]}..." if len(self.content) > 50 else f"{self.sender.full_name}: {self.content}"
    
    def save(self, *args, **kwargs):
        """Update chat room's last message timestamp"""
        super().save(*args, **kwargs)
        self.chat_room.last_message_at = self.created_at
        self.chat_room.save(update_fields=['last_message_at', 'updated_at'])


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
