from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import json
from .models import ChatRoom, Message, MessageReadStatus, ChatParticipant
from accounts.models import User, BusinessInfo
from referr.models import Referral, ReferralAssignment
from .serializers import (
    ChatRoomSerializer, MessageSerializer, 
    ChatRoomListSerializer, MessageCreateSerializer
)
from django.db.models import Count, Q

from django.core.serializers.json import DjangoJSONEncoder

from utils.storage_backends import generate_presigned_url


def serialize_message_with_read_state(msg, viewer, participants):
    """
    Serialize message with dual read perspectives:
    - is_read_by_me: for the viewer (recipient perspective)
    - read_by_*: for the sender (showing who else read their message)
    """
    # Get participant user IDs (excluding sender)
    participant_user_ids = set([p.id for p in participants])
    
    # Get users who read this message (excluding sender)
    read_user_ids = set(msg.read_statuses.values_list("user_id", flat=True))
    read_user_ids.discard(msg.sender_id)
    
    # For the viewer: is this message read by me?
    is_read_by_me = (msg.sender_id == viewer.id) or msg.read_statuses.filter(user_id=viewer.id).exists()
    
    # For the sender: did others read it?
    others_count = len(participant_user_ids - {msg.sender_id})
    read_by_others_count = len(read_user_ids)
    read_by_all_others = (others_count > 0 and read_by_others_count == others_count)
    
    # Get sender image URL
    sender_image_url = (
        generate_presigned_url(f"media/{msg.sender.image}", expires_in=3600)
        if msg.sender.image else None
    )
    
    # Base message data
    message_data = {
        "id": msg.id,
        "room_id": msg.chat_room.room_id,
        "sender": {
            "id": msg.sender.id,
            "name": msg.sender.full_name,
            "role": msg.sender.role,
            "image_url": sender_image_url,
        },
        "content": msg.content,
        "message_type": msg.message_type,
        "created_at": msg.created_at.isoformat(),
        
        # Viewer perspective
        "is_read_by_me": is_read_by_me,
        
        # Sender perspective (for showing "others read" indicators)
        "read_by_user_ids": list(read_user_ids),
        "read_by_others_count": read_by_others_count,
        "read_by_all_others": read_by_all_others,
        
        # Legacy field for backwards compatibility
        "is_read": is_read_by_me,
        "read_by": list(msg.read_statuses.values_list("user_id", flat=True))
    }
    
    # Add file/attachment information for media messages
    if msg.message_type in ['image', 'document', 'file']:
        message_data.update({
            "file_url": msg.get_file_url(),
            "file_name": msg.file_name,
            "file_size": msg.file_size,
            "file_size_formatted": msg.file_size_formatted,
            "file_type": msg.file_type,
            "duration": msg.duration,
            "thumbnail_url": msg.thumbnail_url,
            "dimensions": msg.dimensions,
            "attachments": msg.get_attachments_data()
        })
    
    return message_data


class ChatRoomListView(APIView):
    """
    List all chat rooms for the authenticated user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all chat rooms for the current user"""
        user = request.user

        # Get chat rooms based on user role
        if user.role == 'solo':
            chat_rooms = ChatRoom.objects.filter(solo_user=user)
        elif user.role == 'employee':  # employee role
            chat_rooms = ChatRoom.objects.filter(rep_user=user)
        elif user.role == 'company':
            chat_rooms = ChatRoom.objects.filter(
                Q(company_user=user) |
                Q(rep_user__parent_company=user)
            )
        else:
            chat_rooms = ChatRoom.objects.none()


        # Add unread message count and last message info
        chat_rooms = chat_rooms.annotate(
            unread_count=Count(
                'messages',
                filter=~Q(messages__sender=user) & ~Q(messages__read_statuses__user=user)
            )
        )

        # Custom response format
        rooms_data = [
            {
                "room_id": room.room_id,
                "room_type": room.room_type,
                "chat_name": room.get_display_name(user),
                "last_message": room.get_last_message_summary(),
                "unread_count": room.get_unread_count(user),
                "is_online": room.is_any_participant_online(exclude_user=user),
                "is_active": room.is_active,
                "created_at": room.created_at.isoformat(),
                "updated_at": room.updated_at.isoformat(),
                "referral_id": room.referral.reference_id if room.referral else None,
                "image_url": (
                    generate_presigned_url(f"media/{room.get_chat_image(user)}", expires_in=3600)
                    if room.get_chat_image(user) else None
                ),
            }
            for room in chat_rooms
        ]

        print(f"Chat rooms data in API: {rooms_data}")

        return Response(
            {
                "success": True,
                "chat_rooms": rooms_data,
            },
            status=status.HTTP_200_OK,
        )



class ChatRoomDetailView(APIView):
    """
    Get details of a specific chat room and its messages
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        try:
            chat_room = ChatRoom.objects.get(room_id=room_id)

            # Permission check
            # if not chat_room.can_user_participate(request.user):
            #     return Response({
            #         "success": False,
            #         "error": "You do not have access to this chat room"
            #     }, status=status.HTTP_403_FORBIDDEN)

            # Pagination
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 50))
            offset = (page - 1) * page_size

            messages = (
                Message.objects.filter(chat_room=chat_room)
                .select_related("sender")
                .prefetch_related("read_statuses", "additional_attachments")
                .order_by("-created_at")[offset:offset + page_size]
            )

            messages = list(reversed(messages))  # oldest first

            # Mark as read and send real-time updates
            newly_marked_ids = self._mark_messages_as_read(messages, request.user)
            if newly_marked_ids:
                self._send_read_status_updates_for_detail_view(chat_room, newly_marked_ids, request.user)

            # Get participants for proper read state serialization
            participants = chat_room.get_participants()

            # Room info
            room_data = {
                "room_id": chat_room.room_id,
                "room_type": chat_room.room_type,
                "chat_name": chat_room.get_display_name(request.user),
                "is_active": chat_room.is_active,
                "created_at": chat_room.created_at.isoformat(),
                "updated_at": chat_room.updated_at.isoformat(),
                "referral_id": chat_room.referral.reference_id if chat_room.referral else None,
                "image_url": (
                    generate_presigned_url(f"media/{chat_room.get_chat_image(request.user)}", expires_in=3600)
                    if chat_room.get_chat_image(request.user) else None
                ),
            }

            # Messages with dual read perspectives
            messages_data = [
                serialize_message_with_read_state(msg, request.user, participants)
                for msg in messages
            ]



            

            return Response({
                "success": True,
                "chat_room": room_data,
                "messages": messages_data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "has_more": len(messages) == page_size
                }
            }, status=status.HTTP_200_OK)

        except ChatRoom.DoesNotExist:
            return Response({
                "success": False,
                "error": "Chat room not found"
            }, status=status.HTTP_404_NOT_FOUND)



    def _mark_messages_as_read(self, messages, user):
        """Mark messages as read for the user and return newly marked message IDs"""
        message_ids = [msg.id for msg in messages]
        existing_reads = set(
            MessageReadStatus.objects.filter(
                message_id__in=message_ids, user=user
            ).values_list("message_id", flat=True)
        )

        new_reads = []
        newly_marked_ids = []
        
        for msg in messages:
            if msg.id not in existing_reads and msg.sender != user:
                new_reads.append(MessageReadStatus(message=msg, user=user))
                newly_marked_ids.append(msg.id)

        if new_reads:
            MessageReadStatus.objects.bulk_create(new_reads)
            
        return newly_marked_ids

    def _send_read_status_updates_for_detail_view(self, chat_room, message_ids, user):
        """Send real-time read status updates when messages are read in detail view"""
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
            
            # Get the last (highest) message ID for efficient bulk updates
            last_message_id = max(message_ids) if message_ids else None
            
            # Send read status update to chat room
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_room.room_id}",
                {
                    "type": "message_read_update",
                    "room_id": chat_room.room_id,
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "message_ids": message_ids,
                    "last_read_message_id": last_message_id,
                    "read_at": timezone.now().isoformat(),
                    "timestamp": timezone.now().isoformat(),
                }
            )
            
            # Send chat list updates to all participants (unread count changed)
            self._send_chat_list_updates_for_room(chat_room)
            
        except Exception as e:
            print(f"Error sending read status updates in detail view: {str(e)}")

    def _send_chat_list_updates_for_room(self, chat_room):
        """Send chat list updates to all participants of a specific room"""
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
            
            participants = chat_room.get_participants()
            
            for participant in participants:
                # Create a proper mock request class
                class MockRequest:
                    def __init__(self, user):
                        self.user = user
                        self.META = {'HTTP_HOST': 'thereferralpro.com', 'wsgi.url_scheme': 'https'}

                    def build_absolute_uri(self, location=None):
                        base = "https://thereferralpro.com"
                        return f"{base}{location}" if location else base

                # Serialize the updated chat room list
                mock_request = MockRequest(participant)
                serialized = ChatRoomListSerializer(
                    [chat_room], many=True, context={'request': mock_request}
                ).data
                payload = json.loads(json.dumps(serialized, cls=DjangoJSONEncoder))

                async_to_sync(channel_layer.group_send)(
                    f"chat_list_{participant.id}",
                    {"type": "chat_list_update", "chat_rooms": payload}
                )
                
        except Exception as e:
            print(f"Error sending chat list updates for room: {str(e)}")



from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class CreateChatRoomView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print("CreateChatRoomView POST called")
        print("Request data:", request.data)
        try:
            referral_id = request.data.get('referral_id')
            solo_user_id = request.data.get('solo_user_id')
            
            if not referral_id or not solo_user_id:
                return Response({
                    'success': False,
                    'error': 'referral_id and solo_user_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get referral and solo user
            referral = get_object_or_404(Referral, id=referral_id)
            solo_user = get_object_or_404(User, id=solo_user_id, role='solo')

            print("Authenticated user role:", request.user.role)

            # Case 1: Employee (Rep assigned to referral)
            if request.user.role == 'employee':
                assignment = ReferralAssignment.objects.filter(
                    referral=referral,
                    assigned_to=request.user
                ).first()
                
                if not assignment:
                    return Response({
                        'success': False,
                        'error': 'You are not assigned to this referral'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                chat_room = ChatRoom.create_room_for_referral(
                    referral=referral,
                    solo_user=solo_user,
                    assigned_rep=assignment.assigned_to
                )

            # Case 2: Individual business (Company ↔ Solo)
            elif getattr(request.user, 'business_info', None) and request.user.business_info.biz_type == 'individual':
                chat_room = ChatRoom.create_room_for_referral(
                    referral=referral,
                    solo_user=solo_user
                )

            # Case 3: Other companies must assign a rep
            else:
                return Response({
                    'success': False,
                    'error': 'Non-individual businesses must assign a rep first'
                }, status=status.HTTP_400_BAD_REQUEST)
                    
            # Create participants
            self._create_participant_records(chat_room)
            
            # Send chat list updates to all participants (non-blocking)
            try:
                self._send_chat_list_updates_for_new_room(chat_room)
            except Exception as notification_error:
                print(f"Chat list update error (non-critical): {notification_error}")
            
            serializer = ChatRoomSerializer(chat_room, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Chat room created successfully',
                'chat_room': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error creating chat room: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _send_chat_list_updates_for_new_room(self, chat_room):
        """
        Notify all participants that their chat list has a new/updated room.
        """
        try:
            channel_layer = get_channel_layer()
            participants = chat_room.get_participants()

            # Create a proper mock request class
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                    self.META = {'HTTP_HOST': 'localhost', 'wsgi.url_scheme': 'http'}
                
                def build_absolute_uri(self, location=None):
                    if location:
                        return f"http://localhost{location}"
                    return "http://localhost/"

            from .serializers import ChatRoomListSerializer
            
            for user in participants:
                mock_request = MockRequest(user)
                serialized = ChatRoomListSerializer(
                    [chat_room], many=True, context={'request': mock_request}
                ).data
                payload = json.loads(json.dumps(serialized, cls=DjangoJSONEncoder))

                async_to_sync(channel_layer.group_send)(
                    f"chat_list_{user.id}",
                    {"type": "chat_list_update", "chat_rooms": payload}
                )
        except Exception as e:
            print(f"Error in _send_chat_list_updates_for_new_room: {e}")
            raise

    
    def _create_participant_records(self, chat_room):
        """Create participant records for the chat room"""
        participants = []
        
        # Add solo user as primary participant
        participants.append(ChatParticipant(
            chat_room=chat_room,
            user=chat_room.solo_user,
            role='primary',
            can_send_messages=True
        ))
        
        # Add company user as primary participant
        participants.append(ChatParticipant(
            chat_room=chat_room,
            user=chat_room.company_user,
            role='primary' if chat_room.room_type == 'company_solo' else 'observer',
            can_send_messages=chat_room.room_type == 'company_solo'
        ))
        
        # Add rep user if exists
        if chat_room.rep_user:
            participants.append(ChatParticipant(
                chat_room=chat_room,
                user=chat_room.rep_user,
                role='primary',
                can_send_messages=True
            ))
        
        ChatParticipant.objects.bulk_create(participants, ignore_conflicts=True)

    # def _send_chat_list_updates_for_new_room(self, chat_room):
    #     """Send chat list updates to all participants for a new room"""
    #     try:
    #         from asgiref.sync import async_to_sync
    #         from channels.layers import get_channel_layer
            
    #         channel_layer = get_channel_layer()
            
    #         if not channel_layer:
    #             print("No channel layer configured")
    #             return
            
    #         # Get all participants
    #         participants = chat_room.get_participants()
            
    #         for participant in participants:
    #             # Get updated chat room data for this specific user
    #             user_chat_rooms = self._get_user_chat_rooms_for_create(participant)
                
    #             # Serialize the updated chat room list
    #             serializer = ChatRoomListSerializer(
    #                 user_chat_rooms, 
    #                 many=True, 
    #                 context={'request': type('obj', (object,), {'user': participant})()}
    #             )
                
    #             # Send to user's chat list group
    #             async_to_sync(channel_layer.group_send)(
    #                 f"chat_list_{participant.id}",
    #                 {
    #                     "type": "chat_list_update",
    #                     "chat_rooms": serializer.data
    #                 }
    #             )
                
    #             print(f"Sent new room update to user {participant.id}")
                
    #     except Exception as e:
    #         print(f"Error sending new room updates: {str(e)}")
    #         raise  # Re-raise so the calling code can handle it
    
    def _get_user_chat_rooms_for_create(self, user):
        """Get chat rooms for a specific user based on their role"""
        if user.role == 'solo':
            chat_rooms = ChatRoom.objects.filter(solo_user=user)
        elif user.role == 'rep' or user.role == 'employee':  # employee role
            chat_rooms = ChatRoom.objects.filter(rep_user=user)
        elif user.role == 'company':
            # Company can see their direct rooms and rooms of their reps
            chat_rooms = ChatRoom.objects.filter(
                Q(company_user=user) | 
                Q(rep_user__parent_company=user)
            )
        else:
            chat_rooms = ChatRoom.objects.none()
        
        # Add unread message count and last message info
        chat_rooms = chat_rooms.annotate(
            unread_count=Count(
                'messages', 
                filter=~Q(messages__sender=user) & ~Q(messages__read_statuses__user=user)
            )
        ).select_related(
            'solo_user', 'rep_user', 'company_user', 'referral'
        ).prefetch_related(
            'messages'
        ).order_by('-last_message_at')
        
        return chat_rooms




 
class SendMessageView(APIView):
    """
    Send a message in a chat room
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, room_id):
        """Send a message to the chat room"""
        try:
            chat_room = ChatRoom.objects.get(room_id=room_id)
            
            # Check if user can participate in this room
            # if not chat_room.can_user_participate(request.user):
            #     return Response({
            #         'success': False,
            #         'error': 'You do not have access to this chat room'
            #     }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if user can send messages
            participant = ChatParticipant.objects.filter(
                chat_room=chat_room,
                user=request.user
            ).first()
            
            # if participant and not participant.can_send_messages:
            #     return Response({
            #         'success': False,
            #         'error': 'You do not have permission to send messages in this room'
            #     }, status=status.HTTP_403_FORBIDDEN)
            
            # Create message
            data = request.data.copy()

            # Handle file uploads (single file or multiple files)
            uploaded_files = []
            
            # Handle single file upload
            if 'file' in request.FILES:
                print("Single file upload detected")
                uploaded_files.append(request.FILES['file'])
                data['file'] = request.FILES['file']
            
            # Handle multiple files upload
            if 'files' in request.FILES:
                print("Multiple files upload detected")
                files_list = request.FILES.getlist('files')
                print("Files list:", files_list)
                uploaded_files.extend(files_list)
                print("All uploaded files:", uploaded_files)
                # Don't add files to data since it's not a model field
                # We'll pass it through context instead
            
            # If files were uploaded and message_type not specified, determine it based on first file type
            if uploaded_files and 'message_type' not in data:
                print("Determining message_type based on file content type")
                first_file = uploaded_files[0]
                content_type = getattr(first_file, 'content_type', '')
                
                if content_type.startswith('image/'):
                    print("Setting message_type to 'image'")
                    data['message_type'] = 'image'
                elif content_type.startswith('application/pdf') or content_type.startswith('text/'):
                    print("Setting message_type to 'document'")
                    data['message_type'] = 'document'
                else:
                    print("Setting message_type to 'file'")
                    data['message_type'] = 'file'
            
            
            # Extract files for multiple uploads from data to pass in context
            files_for_context = []
            if 'files' in request.FILES:
                files_for_context = request.FILES.getlist('files')
            
            serializer = MessageCreateSerializer(
                data=data,
                context={
                    'chat_room': chat_room, 
                    'sender': request.user,
                    'files': files_for_context
                }
            )
            
            if serializer.is_valid():
                print("Serializer is valid, saving message...")
                message = serializer.save()
                print(f"Message saved with ID: {message.id}")
                
                # Send chat list updates to all participants
                try:
                    self._send_chat_list_updates(chat_room)
                except Exception as notification_error:
                    print(f"Notification error (non-critical): {notification_error}")
                
                response_serializer = MessageSerializer(message, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'Message sent successfully',
                    'data': response_serializer.data
                }, status=200)
            else:
                print("Serializer validation failed:")
                print("Errors:", serializer.errors)
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ChatRoom.DoesNotExist as e:
            print(f"ChatRoom not found: {str(e)}")
            return Response({
                'success': False,
                'error': 'Chat room not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error in SendMessageView: {str(e)}")
            return Response({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _send_chat_list_updates(self, chat_room):
        """Send chat list updates to all participants"""
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            
            if not channel_layer:
                print("No channel layer configured")
                return
            
            # Create a proper mock request class
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                    self.META = {
                        'HTTP_HOST': 'thereferralpro.com',
                        'wsgi.url_scheme': 'https'
                    }

                def build_absolute_uri(self, location=None):
                    base = "https://thereferralpro.com"
                    return f"{base}{location}" if location else base

            
            # Get all participants
            participants = chat_room.get_participants()
            
            for participant in participants:
                # Get updated chat room data for this specific user
                user_chat_rooms = self._get_user_chat_rooms(participant)

                # Serialize the updated chat room list with proper mock request
                mock_request = MockRequest(participant)
                serialized = ChatRoomListSerializer(
                    [chat_room], many=True, context={'request': mock_request}
                ).data
                payload = json.loads(json.dumps(serialized, cls=DjangoJSONEncoder))

                async_to_sync(channel_layer.group_send)(
                    f"chat_list_{participant.id}",
                    {"type": "chat_list_update", "chat_rooms": payload}
                )

                print(f"Sent chat list update to user {participant.id}")

                
        except Exception as e:
            print(f"Error sending chat list updates: {str(e)}")
            raise  # Re-raise so the calling code can handle it
    
    def _get_user_chat_rooms(self, user):
        """Get chat rooms for a specific user based on their role"""
        if user.role == 'solo':
            chat_rooms = ChatRoom.objects.filter(solo_user=user)
        elif user.role == 'employee':  # employee role
            chat_rooms = ChatRoom.objects.filter(rep_user=user)
        elif user.role == 'company':
            # Company can see their direct rooms and rooms of their reps
            chat_rooms = ChatRoom.objects.filter(
                Q(company_user=user) | 
                Q(rep_user__parent_company=user)
            )
        else:
            chat_rooms = ChatRoom.objects.none()
        
        # Add unread message count and last message info
        chat_rooms = chat_rooms.annotate(
            unread_count=Count(
                'messages', 
                filter=~Q(messages__sender=user) & ~Q(messages__read_statuses__user=user)
            )
        ).select_related(
            'solo_user', 'rep_user', 'company_user', 'referral'
        ).prefetch_related(
            'messages'
        ).order_by('-last_message_at')
        
        return chat_rooms





class ChatAnalyticsView(APIView):
    """
    Get chat analytics and statistics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get chat analytics for the user"""
        user = request.user
        
        # Base query for user's chat rooms
        if user.role == 'solo':
            chat_rooms = ChatRoom.objects.filter(solo_user=user)
        elif user.role == 'rep':
            chat_rooms = ChatRoom.objects.filter(rep_user=user)
        elif user.role == 'company':
            chat_rooms = ChatRoom.objects.filter(
                Q(company_user=user) | 
                Q(rep_user__parent_company=user)
            )
        else:
            chat_rooms = ChatRoom.objects.none()
        
        # Calculate analytics
        total_rooms = chat_rooms.count()
        active_rooms = chat_rooms.filter(is_active=True).count()
        
        # Messages sent in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_messages = Message.objects.filter(
            chat_room__in=chat_rooms,
            created_at__gte=thirty_days_ago
        ).count()
        
        # Unread messages
        unread_messages = Message.objects.filter(
            chat_room__in=chat_rooms
        ).exclude(
            read_statuses__user=user
        ).exclude(
            sender=user
        ).count()
        
        # Active conversations (had activity in last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        active_conversations = chat_rooms.filter(
            last_message_at__gte=seven_days_ago
        ).count()
        
        return Response({
            'success': True,
            'analytics': {
                'total_chat_rooms': total_rooms,
                'active_chat_rooms': active_rooms,
                'messages_last_30_days': recent_messages,
                'unread_messages': unread_messages,
                'active_conversations_last_7_days': active_conversations
            }
        }, status=status.HTTP_200_OK)


class MarkMessagesReadView(APIView):
    """
    Mark one or multiple messages as read
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, room_id):
        """Mark messages as read in a chat room"""
        try:
            chat_room = ChatRoom.objects.get(room_id=room_id)
            
            # Check if user can participate in this room
            if not chat_room.can_user_participate(request.user):
                return Response({
                    'success': False,
                    'error': 'You do not have access to this chat room'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get message IDs from request
            message_id = request.data.get('message_id')
            message_ids = request.data.get('message_ids', [])
            
            # Support both single message and bulk marking
            if message_id:
                message_ids = [message_id]
            
            if not message_ids:
                return Response({
                    'success': False,
                    'error': 'No message IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get messages that exist in this room and aren't sent by current user
            messages = Message.objects.filter(
                id__in=message_ids,
                chat_room=chat_room
            ).exclude(sender=request.user)
            
            # Get existing read statuses to avoid duplicates
            existing_reads = set(
                MessageReadStatus.objects.filter(
                    message__in=messages,
                    user=request.user
                ).values_list("message_id", flat=True)
            )
            
            # Create new read statuses for unread messages
            new_reads = []
            marked_message_ids = []
            
            for message in messages:
                if message.id not in existing_reads:
                    new_reads.append(MessageReadStatus(message=message, user=request.user))
                    marked_message_ids.append(message.id)
                else:
                    # Already read, but include in response for consistency
                    marked_message_ids.append(message.id)
            
            if new_reads:
                MessageReadStatus.objects.bulk_create(new_reads)
            
            # Send real-time updates if any messages were newly marked as read
            if new_reads:
                self._send_read_status_updates(chat_room, marked_message_ids, request.user)
            
            return Response({
                'success': True,
                'message': f'Marked {len(marked_message_ids)} messages as read',
                'marked_message_ids': marked_message_ids
            }, status=status.HTTP_200_OK)
            
        except ChatRoom.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Chat room not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to mark messages as read: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _send_read_status_updates(self, chat_room, message_ids, user):
        """Send real-time read status updates to WebSocket consumers"""
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
            
            # Get the last (highest) message ID for efficient bulk updates
            last_message_id = max(message_ids) if message_ids else None
            
            # Send read status update to chat room
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_room.room_id}",
                {
                    "type": "message_read_update",
                    "room_id": chat_room.room_id,
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "message_ids": message_ids,
                    "last_read_message_id": last_message_id,
                    "read_at": timezone.now().isoformat(),
                    "timestamp": timezone.now().isoformat(),
                }
            )
            
            # Send chat list updates to all participants (unread count changed)
            participants = chat_room.get_participants()
            for participant in participants:
                # Get updated chat room data for this specific user
                user_chat_rooms = self._get_user_chat_rooms_for_read_update(participant)
                
                # Create a proper mock request class
                class MockRequest:
                    def __init__(self, user):
                        self.user = user
                        self.META = {'HTTP_HOST': 'thereferralpro.com', 'wsgi.url_scheme': 'https'}

                    def build_absolute_uri(self, location=None):
                        base = "https://thereferralpro.com"
                        return f"{base}{location}" if location else base

                # Serialize the updated chat room list
                mock_request = MockRequest(participant)
                serialized = ChatRoomListSerializer(
                    [chat_room], many=True, context={'request': mock_request}
                ).data
                payload = json.loads(json.dumps(serialized, cls=DjangoJSONEncoder))

                async_to_sync(channel_layer.group_send)(
                    f"chat_list_{participant.id}",
                    {"type": "chat_list_update", "chat_rooms": payload}
                )
            
        except Exception as e:
            print(f"Error sending read status updates: {str(e)}")
    
    def _get_user_chat_rooms_for_read_update(self, user):
        """Get chat rooms for a specific user based on their role"""
        if user.role == 'solo':
            chat_rooms = ChatRoom.objects.filter(solo_user=user)
        elif user.role == 'employee':
            chat_rooms = ChatRoom.objects.filter(rep_user=user)
        elif user.role == 'company':
            chat_rooms = ChatRoom.objects.filter(
                Q(company_user=user) | 
                Q(rep_user__parent_company=user)
            )
        else:
            chat_rooms = ChatRoom.objects.none()
        
        # Add unread message count and last message info
        chat_rooms = chat_rooms.annotate(
            unread_count=Count(
                'messages', 
                filter=~Q(messages__sender=user) & ~Q(messages__read_statuses__user=user)
            )
        ).select_related(
            'solo_user', 'rep_user', 'company_user', 'referral'
        ).prefetch_related(
            'messages'
        ).order_by('-last_message_at')
        
        return chat_rooms


class MarkAllMessagesReadView(APIView):
    """
    Mark all messages in a chat room as read
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, room_id):
        """Mark all unread messages in a chat room as read"""
        try:
            chat_room = ChatRoom.objects.get(room_id=room_id)
            
            # Check if user can participate in this room
            if not chat_room.can_user_participate(request.user):
                return Response({
                    'success': False,
                    'error': 'You do not have access to this chat room'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get all unread messages in this room (excluding user's own messages)
            unread_messages = Message.objects.filter(
                chat_room=chat_room
            ).exclude(
                sender=request.user
            ).exclude(
                read_statuses__user=request.user
            )
            
            if not unread_messages.exists():
                return Response({
                    'success': True,
                    'message': 'No unread messages to mark',
                    'marked_count': 0
                }, status=status.HTTP_200_OK)
            
            # Create read statuses for all unread messages
            new_reads = [
                MessageReadStatus(message=msg, user=request.user)
                for msg in unread_messages
            ]
            
            MessageReadStatus.objects.bulk_create(new_reads)
            marked_message_ids = [msg.id for msg in unread_messages]
            
            # Send real-time updates
            self._send_read_status_updates_for_all_messages(chat_room, marked_message_ids, request.user)
            
            return Response({
                'success': True,
                'message': f'Marked {len(marked_message_ids)} messages as read',
                'marked_count': len(marked_message_ids),
                'marked_message_ids': marked_message_ids
            }, status=status.HTTP_200_OK)
            
        except ChatRoom.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Chat room not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to mark all messages as read: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _send_read_status_updates_for_all_messages(self, chat_room, message_ids, user):
        """Send real-time read status updates when all messages are marked as read"""
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if not channel_layer:
                return
            
            # Use cutoff pointer for efficient bulk updates
            last_message_id = max(message_ids) if message_ids else None
            
            # Send read status update to chat room
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_room.room_id}",
                {
                    "type": "message_read_update",
                    "room_id": chat_room.room_id,
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "message_ids": message_ids,
                    "last_read_message_id": last_message_id,
                    "read_at": timezone.now().isoformat(),
                    "timestamp": timezone.now().isoformat(),
                    "mark_all": True  # Flag to indicate this was a "mark all" operation
                }
            )
            
            # Send chat list updates to all participants (unread count changed to 0 for this user)
            participants = chat_room.get_participants()
            for participant in participants:
                # Create a proper mock request class
                class MockRequest:
                    def __init__(self, user):
                        self.user = user
                        self.META = {'HTTP_HOST': 'thereferralpro.com', 'wsgi.url_scheme': 'https'}

                    def build_absolute_uri(self, location=None):
                        base = "https://thereferralpro.com"
                        return f"{base}{location}" if location else base

                # Serialize the updated chat room list
                mock_request = MockRequest(participant)
                serialized = ChatRoomListSerializer(
                    [chat_room], many=True, context={'request': mock_request}
                ).data
                payload = json.loads(json.dumps(serialized, cls=DjangoJSONEncoder))

                async_to_sync(channel_layer.group_send)(
                    f"chat_list_{participant.id}",
                    {"type": "chat_list_update", "chat_rooms": payload}
                )
            
        except Exception as e:
            print(f"Error sending read status updates for all messages: {str(e)}")


class UpdateChatRoomView(APIView):
    """
    Update chat room settings
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, room_id):
        """Update chat room settings"""
        try:
            chat_room = ChatRoom.objects.get(room_id=room_id)
            
            # Check permissions - only company owners can update room settings
            if request.user.role != 'company' or chat_room.company_user != request.user:
                return Response({
                    'success': False,
                    'error': 'Only the company owner can update room settings'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Update allowed fields
            is_active = request.data.get('is_active')
            if is_active is not None:
                chat_room.is_active = is_active
                chat_room.save()
            
            serializer = ChatRoomSerializer(chat_room, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Chat room updated successfully',
                'chat_room': serializer.data
            }, status=status.HTTP_200_OK)
            
        except ChatRoom.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Chat room not found'
            }, status=status.HTTP_404_NOT_FOUND)
