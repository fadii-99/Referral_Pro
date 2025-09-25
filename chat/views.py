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
        try:
            chat_room = ChatRoom.objects.get(room_id=room_id)
            
            # Check if user can access this room
            if not chat_room.can_user_participate(request.user):
                return Response({
                    'success': False,
                    'error': 'You do not have access to this chat room'
                }, status=status.HTTP_403_FORBIDDEN)
            
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
            
            # Serialize data
            room_serializer = ChatRoomSerializer(chat_room, context={'request': request})
            message_serializer = MessageSerializer(messages, many=True, context={'request': request})
            
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
            
        except ChatRoom.DoesNotExist:
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


class CreateChatRoomView(APIView):
    """
    Create a new chat room for a referral
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a chat room for a referral"""
        try:
            referral_id = request.data.get('referral_id')
            solo_user_id = request.data.get('solo_user_id')
            
            if not referral_id or not solo_user_id:
                return Response({
                    'success': False,
                    'error': 'referral_id and solo_user_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the referral and solo user
            referral = get_object_or_404(Referral, id=referral_id)
            solo_user = get_object_or_404(User, id=solo_user_id, role='solo')
            
            # Check permissions based on user role
            if request.user.role == 'company':
                # Company creating room - check if it's their referral
                if referral.company != request.user:
                    return Response({
                        'success': False,
                        'error': 'You can only create rooms for your own referrals'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Check business type
                business_info = getattr(request.user, 'business_info', None)
                if business_info and business_info.biz_type == 'individual':
                    # Individual business - direct company to solo chat
                    chat_room = ChatRoom.create_room_for_referral(
                        referral=referral,
                        solo_user=solo_user
                    )
                else:
                    return Response({
                        'success': False,
                        'error': 'Non-individual businesses must assign a rep first'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            elif request.user.role == 'rep':  # employee
                # Rep creating room - check if they're assigned to this referral
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
                    assigned_rep=request.user
                )
                
            else:
                return Response({
                    'success': False,
                    'error': 'Only companies and reps can create chat rooms'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Create participant records
            self._create_participant_records(chat_room)
            
            serializer = ChatRoomSerializer(chat_room, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Chat room created successfully',
                'chat_room': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
            serializer = MessageCreateSerializer(data=request.data)
            if serializer.is_valid():
                message = serializer.save(
                    chat_room=chat_room,
                    sender=request.user
                )
                
                # Send notification to other participants
                self._send_message_notifications(chat_room, message)
                
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
                
        except ChatRoom.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Chat room not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _send_message_notifications(self, chat_room, message):
        """Send notifications to other participants about new message"""
        from channels.layers import get_channel_layer
        import asyncio
        
        channel_layer = get_channel_layer()
        
        # Get all participants except the sender
        participants = chat_room.get_participants()
        
        for participant in participants:
            if participant != message.sender:
                # Send WebSocket notification
                notification_group = f'notifications_{participant.id}'
                
                asyncio.create_task(
                    channel_layer.group_send(
                        notification_group,
                        {
                            'type': 'new_message_notification',
                            'chat_room_id': chat_room.room_id,
                            'sender_name': message.sender.full_name,
                            'message_preview': message.content[:100],
                            'timestamp': message.created_at.isoformat()
                        }
                    )
                )


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
