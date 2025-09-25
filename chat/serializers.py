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
    """Serializer for chat messages"""
    sender = UserBasicSerializer(read_only=True)
    is_read = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'message_type', 'content', 'file_url', 
            'file_name', 'file_size', 'is_edited', 'edited_at', 
            'created_at', 'is_read', 'read_count'
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


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    
    class Meta:
        model = Message
        fields = ['content', 'message_type', 'file_url', 'file_name', 'file_size']
    
    def validate_content(self, value):
        """Validate message content"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        if len(value) > 5000:  # Reasonable limit
            raise serializers.ValidationError("Message content is too long")
        return value.strip()


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
            return {
                'id': last_message.id,
                'content': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
                'sender_name': last_message.sender.full_name,
                'message_type': last_message.message_type,
                'created_at': last_message.created_at
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
            return {
                'content': last_message.content[:50] + '...' if len(last_message.content) > 50 else last_message.content,
                'sender_name': last_message.sender.full_name,
                'created_at': last_message.created_at
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