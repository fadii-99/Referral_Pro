from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, MessageReadStatus, ChatParticipant
from accounts.models import BusinessInfo
from referr.models import Referral

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for chat contexts"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'image']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Include image URL if exists
        if instance.image:
            data['image'] = instance.image.url
        return data


class ReferralBasicSerializer(serializers.ModelSerializer):
    """Basic referral serializer for chat contexts"""
    
    class Meta:
        model = Referral
        fields = ['id', 'reference_id', 'service_type', 'status', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages with comprehensive media support"""
    sender = UserBasicSerializer(read_only=True)
    is_read = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    reply_to = serializers.SerializerMethodField()
    file_size_formatted = serializers.CharField(source='file_size_formatted', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'message_type', 'content', 'file_url', 
            'file_name', 'file_size', 'file_size_formatted', 'file_type',
            'duration', 'thumbnail_url', 'dimensions', 'is_edited', 
            'edited_at', 'created_at', 'is_read', 'read_count', 'reply_to'
        ]
    
    def get_is_read(self, obj):
        """Check if current user has read this message"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return MessageReadStatus.objects.filter(
                message=obj, 
                user=request.user
            ).exists()
        return False
    
    def get_read_count(self, obj):
        """Get total read count for this message"""
        return obj.read_statuses.count()
    
    def get_reply_to(self, obj):
        """Get reply message info if this message is a reply"""
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'content': obj.reply_to.content[:100] if obj.reply_to.content else '',
                'sender_name': obj.reply_to.sender.full_name,
                'message_type': obj.reply_to.message_type,
                'file_name': obj.reply_to.file_name if obj.reply_to.is_media else None
            }
        return None


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat messages with media support"""
    reply_to_id = serializers.IntegerField(required=False, write_only=True)
    
    class Meta:
        model = Message
        fields = [
            'message_type', 'content', 'file_url', 'file_name', 'file_size',
            'file_type', 'duration', 'thumbnail_url', 'dimensions', 'reply_to_id'
        ]
    
    def validate(self, data):
        """Validate message data"""
        message_type = data.get('message_type', 'text')
        content = data.get('content', '').strip()
        file_url = data.get('file_url')
        
        # Text messages must have content
        if message_type == 'text' and not content:
            raise serializers.ValidationError("Text messages cannot be empty")
        
        # Media messages must have file_url
        if message_type in ['image', 'video', 'audio', 'document', 'file'] and not file_url:
            raise serializers.ValidationError(f"{message_type.title()} messages require a file")
        
        return data
    
    def validate_reply_to_id(self, value):
        """Validate reply message exists in the same chat room"""
        if value:
            chat_room = self.context.get('chat_room')
            if not chat_room:
                raise serializers.ValidationError("Chat room context required for reply messages")
            
            try:
                reply_message = Message.objects.get(id=value, chat_room=chat_room)
                return reply_message
            except Message.DoesNotExist:
                raise serializers.ValidationError("Reply message not found in this chat room")
        return None

    def create(self, validated_data):
        """Create message with proper context"""
        chat_room = self.context.get('chat_room')
        sender = self.context.get('sender')
        reply_to = validated_data.pop('reply_to_id', None)
        
        return Message.objects.create(
            chat_room=chat_room,
            sender=sender,
            reply_to=reply_to,
            **validated_data
        )


class ChatParticipantSerializer(serializers.ModelSerializer):
    """Serializer for chat participants"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChatParticipant
        fields = [
            'user', 'role', 'can_send_messages', 'can_view_history',
            'joined_at', 'last_seen_at', 'is_online'
        ]


class ChatRoomSerializer(serializers.ModelSerializer):
    """Detailed chat room serializer"""
    solo_user = UserBasicSerializer(read_only=True)
    rep_user = UserBasicSerializer(read_only=True)
    company_user = UserBasicSerializer(read_only=True)
    referral = ReferralBasicSerializer(read_only=True)
    participants = ChatParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    can_send_messages = serializers.SerializerMethodField()
    business_type = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_id', 'room_type', 'solo_user', 'rep_user', 
            'company_user', 'referral', 'is_active', 'created_at', 
            'updated_at', 'last_message_at', 'participants', 
            'last_message', 'unread_count', 'can_send_messages',
            'business_type'
        ]
    
    def get_last_message(self, obj):
        """Get the last message in this room"""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            content = last_message.content
            if last_message.message_type != 'text':
                content = f"[{last_message.message_type.upper()}] {last_message.file_name or 'Media file'}"
            elif len(content) > 100:
                content = content[:100] + '...'
                
            return {
                'id': last_message.id,
                'content': content,
                'sender_name': last_message.sender.full_name,
                'message_type': last_message.message_type,
                'created_at': last_message.created_at,
                'file_name': last_message.file_name if last_message.is_media else None
            }
        return None
    
    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.messages.exclude(
                read_statuses__user=request.user
            ).exclude(
                sender=request.user
            ).count()
        return 0
    
    def get_can_send_messages(self, obj):
        """Check if current user can send messages in this room"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            participant = obj.participants.filter(user=request.user).first()
            if participant:
                return participant.can_send_messages
            return obj.can_user_participate(request.user)
        return False
    
    def get_business_type(self, obj):
        """Get the business type of the company"""
        if hasattr(obj.company_user, 'business_info'):
            return obj.company_user.business_info.biz_type
        return None


class ChatRoomListSerializer(serializers.ModelSerializer):
    """Simplified chat room serializer for list views"""
    solo_user = UserBasicSerializer(read_only=True)
    rep_user = UserBasicSerializer(read_only=True)
    company_user = UserBasicSerializer(read_only=True)
    referral = ReferralBasicSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_id', 'room_type', 'solo_user', 'rep_user', 
            'company_user', 'referral', 'is_active', 'last_message_at',
            'last_message', 'unread_count', 'other_participant',
            'company_name'
        ]
    
    def get_last_message(self, obj):
        """Get the last message in this room"""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            content = last_message.content
            if last_message.message_type != 'text':
                content = f"[{last_message.message_type.upper()}] {last_message.file_name or 'Media file'}"
            elif len(content) > 50:
                content = content[:50] + '...'
                
            return {
                'content': content,
                'sender_name': last_message.sender.full_name,
                'created_at': last_message.created_at,
                'message_type': last_message.message_type
            }
        return None
    
    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.messages.exclude(
                read_statuses__user=request.user
            ).exclude(
                sender=request.user
            ).count()
        return 0
    
    def get_other_participant(self, obj):
        """Get the main other participant for current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            current_user = request.user
            
            if current_user.role == 'solo':
                # For solo users, show rep or company
                if obj.rep_user:
                    return UserBasicSerializer(obj.rep_user).data
                else:
                    return UserBasicSerializer(obj.company_user).data
            elif current_user.role == 'rep':
                # For reps, show solo user
                return UserBasicSerializer(obj.solo_user).data
            elif current_user.role == 'company':
                # For companies, show solo user
                return UserBasicSerializer(obj.solo_user).data
        
        return None
    
    def get_company_name(self, obj):
        """Get company name from business info"""
        if hasattr(obj.company_user, 'business_info'):
            return obj.company_user.business_info.company_name
        return obj.company_user.full_name


class ChatRoomCreateSerializer(serializers.Serializer):
    """Serializer for creating chat rooms"""
    referral_id = serializers.IntegerField()
    solo_user_id = serializers.IntegerField()
    
    def validate_referral_id(self, value):
        """Validate referral exists"""
        try:
            Referral.objects.get(id=value)
            return value
        except Referral.DoesNotExist:
            raise serializers.ValidationError("Referral not found")
    
    def validate_solo_user_id(self, value):
        """Validate solo user exists"""
        try:
            user = User.objects.get(id=value, role='solo')
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Solo user not found")


class ChatStatisticsSerializer(serializers.Serializer):
    """Serializer for chat statistics"""
    total_chat_rooms = serializers.IntegerField()
    active_chat_rooms = serializers.IntegerField()
    messages_last_30_days = serializers.IntegerField()
    unread_messages = serializers.IntegerField()
    active_conversations_last_7_days = serializers.IntegerField()