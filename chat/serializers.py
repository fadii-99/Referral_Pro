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
    sender = UserBasicSerializer(read_only=True)
    is_read = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_size_formatted = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'message_type', 'content',
            'file_url', 'file_name', 'file_size', 'file_size_formatted', 'file_type',
            'thumbnail_url', 'duration', 'dimensions', 'attachments',
            'is_edited', 'edited_at', 'created_at',
            'is_read', 'read_count',
        ]

    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.read_statuses.filter(user=request.user).exists()
        return False

    def get_read_count(self, obj):
        return obj.read_statuses.count()
        
    def get_file_url(self, obj):
        """Get presigned URL for file access"""
        return obj.get_file_url()
    
    def get_file_size_formatted(self, obj):
        """Format file size to be human-readable"""
        if obj.file_size is None:
            return None
            
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0 or unit == 'TB':
                return f"{size:.1f} {unit}"
            size /= 1024.0
    
    def get_attachments(self, obj):
        """Get all attachments for this message"""
        return obj.get_attachments_data()




class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat messages with media support"""
    reply_to_id = serializers.IntegerField(required=False, write_only=True)
    file = serializers.FileField(required=False, write_only=True)
    # Remove the ListField approach as it doesn't work well with multipart form data
    # We'll handle multiple files directly in the view
    
    class Meta:
        model = Message
        fields = [
            'message_type', 'content', 'attachment', 'file_name', 'file_size',
            'file_type', 'duration', 'thumbnail_url', 'dimensions', 'reply_to_id',
            'file'
        ]
    
    def validate(self, data):
        """Validate message data"""
        message_type = data.get('message_type', 'text')
        content = data.get('content', '').strip()
        attachment = data.get('attachment')
        file = data.get('file')
        
        # Get files from context (passed from view)
        files = self.context.get('files', [])
        
        # Text messages must have content (unless they have attachments)
        if message_type == 'text' and not content and not file and not files:
            raise serializers.ValidationError("Text messages cannot be empty unless they have attachments")
        
        # Media messages must have file, files, or attachment
        if message_type in ['image', 'video', 'audio', 'document', 'file']:
            if not file and not files and not attachment:
                raise serializers.ValidationError(f"{message_type.title()} messages require at least one file")
        
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
        from .models import MessageAttachment
        
        chat_room = self.context.get('chat_room')
        sender = self.context.get('sender')
        reply_to = validated_data.pop('reply_to_id', None)
        
        # Handle single file upload
        file = validated_data.pop('file', None)
        
        # Get multiple files from context (passed from view)
        files = self.context.get('files', [])
        
        # Combine single file with multiple files
        all_files = []
        if file:
            all_files.append(file)
        if files:
            all_files.extend(files)
        
        # If we have files, determine message type from the first file if not specified
        if all_files and 'message_type' not in validated_data:
            first_file = all_files[0]
            content_type = getattr(first_file, 'content_type', '')
            if content_type.startswith('image/'):
                validated_data['message_type'] = 'image'
            elif content_type.startswith('video/'):
                validated_data['message_type'] = 'video'
            elif content_type.startswith('audio/'):
                validated_data['message_type'] = 'audio'
            else:
                validated_data['message_type'] = 'file'
        
        # Handle first file as primary attachment
        if all_files:
            first_file = all_files[0]
            validated_data['attachment'] = first_file
            validated_data['file_name'] = first_file.name
            validated_data['file_size'] = first_file.size
            validated_data['file_type'] = getattr(first_file, 'content_type', 'application/octet-stream')
        
        # Create the message
        message = Message.objects.create(
            chat_room=chat_room,
            sender=sender,
            reply_to=reply_to,
            **validated_data
        )
        
        # Create additional attachments for remaining files
        if len(all_files) > 1:
            additional_attachments = []
            for additional_file in all_files[1:]:
                attachment = MessageAttachment(
                    message=message,
                    attachment=additional_file,
                    file_name=additional_file.name,
                    file_size=additional_file.size,
                    file_type=getattr(additional_file, 'content_type', 'application/octet-stream')
                )
                additional_attachments.append(attachment)
            
            MessageAttachment.objects.bulk_create(additional_attachments)
        
        return message


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