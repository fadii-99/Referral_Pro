from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import ChatRoom, Message, MessageReadStatus, ChatParticipant
from accounts.models import User, BusinessInfo
from referr.models import Referral, ReferralAssignment
from .serializers import (
    ChatRoomSerializer, MessageSerializer, 
    ChatRoomListSerializer, MessageCreateSerializer
)


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
        elif user.role == 'rep':  # employee role
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
                filter=~Q(messages__read_statuses__user=user)
            )
        ).select_related(
            'solo_user', 'rep_user', 'company_user', 'referral'
        ).prefetch_related(
            'messages'
        ).order_by('-last_message_at')
        
        serializer = ChatRoomListSerializer(chat_rooms, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'chat_rooms': serializer.data
        }, status=status.HTTP_200_OK)


class ChatRoomDetailView(APIView):
    """
    Get details of a specific chat room and its messages
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, room_id):
        """Get chat room details and messages"""
        print("roommmmscjbas ",room_id)
        try:
            chat_room = ChatRoom.objects.get(room_id=room_id)
            
            # Check if user can access this room
            if not chat_room.can_user_participate(request.user):
                return Response({
                    'success': False,
                    'error': 'You do not have access to this chat room'
                }, status=status.HTTP_403_FORBIDDEN)

            print(f"Fetching messages for room {room_id} for user {request.user.id}")
            # Get messages with pagination
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 50))
            offset = (page - 1) * page_size
            
            messages = Message.objects.filter(chat_room=chat_room)\
                .select_related('sender')\
                .prefetch_related('read_statuses')\
                .order_by('-created_at')[offset:offset + page_size]
            
            # Reverse to show oldest first
            messages = list(reversed(messages))
            
            # Mark messages as read for current user
            self._mark_messages_as_read(messages, request.user)
            print(f"Marked {len(messages)} messages as read for user {request.user.id}")
            # Serialize data
            try:
                room_serializer = ChatRoomSerializer(chat_room, context={'request': request})
            except Exception as e:
                print(f"Error serializing chat room: {str(e)}")
            try:
                message_serializer = MessageSerializer(messages, many=True, context={'request': request})
            except Exception as e:
                print(f"Error serializing chat room: {str(e)}")
            
            return Response({
                'success': True,
                'chat_room': room_serializer.data,
                'messages': message_serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'has_more': len(messages) == page_size
                }
            }, status=status.HTTP_200_OK)
            
        except ChatRoom.DoesNotExist as e:
            print(f"ChatRoom not found: {str(e)}")
            return Response({
                'success': False,
                'error': 'Chat room not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _mark_messages_as_read(self, messages, user):
        """Mark messages as read for the user"""
        message_ids = [msg.id for msg in messages]
        existing_reads = set(
            MessageReadStatus.objects.filter(
                message_id__in=message_ids, 
                user=user
            ).values_list('message_id', flat=True)
        )
        
        new_reads = []
        for message in messages:
            if message.id not in existing_reads and message.sender != user:
                new_reads.append(
                    MessageReadStatus(message=message, user=user)
                )
        
        if new_reads:
            MessageReadStatus.objects.bulk_create(new_reads)


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
                    [chat_room], 
                    many=True, 
                    context={'request': mock_request}
                ).data

                async_to_sync(channel_layer.group_send)(
                    f"chat_list_{user.id}",
                    {
                        "type": "chat_list_update",
                        "chat_rooms": serialized,
                    }
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
                filter=~Q(messages__read_statuses__user=user)
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
            if not chat_room.can_user_participate(request.user):
                return Response({
                    'success': False,
                    'error': 'You do not have access to this chat room'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if user can send messages
            participant = ChatParticipant.objects.filter(
                chat_room=chat_room,
                user=request.user
            ).first()
            
            if participant and not participant.can_send_messages:
                return Response({
                    'success': False,
                    'error': 'You do not have permission to send messages in this room'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Create message
            serializer = MessageCreateSerializer(
                data=request.data,
                context={'chat_room': chat_room, 'sender': request.user}
            )
            if serializer.is_valid():
                message = serializer.save()
                
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
                }, status=status.HTTP_201_CREATED)
            else:
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
                    self.META = {'HTTP_HOST': 'localhost', 'wsgi.url_scheme': 'http'}
                
                def build_absolute_uri(self, location=None):
                    if location:
                        return f"http://localhost{location}"
                    return "http://localhost/"
            
            # Get all participants
            participants = chat_room.get_participants()
            
            for participant in participants:
                # Get updated chat room data for this specific user
                user_chat_rooms = self._get_user_chat_rooms(participant)
                
                # Serialize the updated chat room list with proper mock request
                mock_request = MockRequest(participant)
                serializer = ChatRoomListSerializer(
                    user_chat_rooms, 
                    many=True, 
                    context={'request': mock_request}
                )
                
                # Send to user's chat list group
                async_to_sync(channel_layer.group_send)(
                    f"chat_list_{participant.id}",
                    {
                        "type": "chat_list_update",
                        "chat_rooms": serializer.data
                    }
                )
                
                print(f"Sent chat list update to user {participant.id}")
                
        except Exception as e:
            print(f"Error sending chat list updates: {str(e)}")
            raise  # Re-raise so the calling code can handle it
    
    def _get_user_chat_rooms(self, user):
        """Get chat rooms for a specific user based on their role"""
        if user.role == 'solo':
            chat_rooms = ChatRoom.objects.filter(solo_user=user)
        elif user.role == 'rep':  # employee role
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
                filter=~Q(messages__read_statuses__user=user)
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
