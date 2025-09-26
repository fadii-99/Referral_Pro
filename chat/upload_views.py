import os
import mimetypes
from PIL import Image
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
import uuid


class MediaUploadView(APIView):
    """
    Handle file uploads for chat messages (images, videos, audio, documents)
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    # File size limits (in bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20MB
    
    # Allowed file types
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/ogg', 'video/avi', 'video/mov']
    ALLOWED_AUDIO_TYPES = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/webm']
    ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                             'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             'text/plain', 'text/csv']
    
    def post(self, request):
        """Upload a media file for chat"""
        try:
            if 'file' not in request.FILES:
                return Response({
                    'success': False,
                    'error': 'No file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            file_type = request.data.get('file_type', self._detect_file_type(file))
            
            # Validate file type and size
            validation_result = self._validate_file(file, file_type)
            if not validation_result['valid']:
                return Response({
                    'success': False,
                    'error': validation_result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate unique filename
            file_extension = os.path.splitext(file.name)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Determine upload path based on file type
            upload_path = self._get_upload_path(file_type, unique_filename)
            
            # Save file
            file_path = default_storage.save(upload_path, ContentFile(file.read()))
            file_url = default_storage.url(file_path)
            
            # Process file metadata
            metadata = self._process_file_metadata(file, file_type, file_path)
            
            response_data = {
                'success': True,
                'file_data': {
                    'file_url': file_url,
                    'file_name': file.name,
                    'file_size': file.size,
                    'file_type': file.content_type,
                    'message_type': file_type,
                    **metadata
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Upload failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _detect_file_type(self, file):
        """Detect file type based on MIME type"""
        mime_type = file.content_type or mimetypes.guess_type(file.name)[0]
        
        if mime_type in self.ALLOWED_IMAGE_TYPES:
            return 'image'
        elif mime_type in self.ALLOWED_VIDEO_TYPES:
            return 'video'
        elif mime_type in self.ALLOWED_AUDIO_TYPES:
            return 'audio'
        elif mime_type in self.ALLOWED_DOCUMENT_TYPES:
            return 'document'
        else:
            return 'file'
    
    def _validate_file(self, file, file_type):
        """Validate file size and type"""
        mime_type = file.content_type or mimetypes.guess_type(file.name)[0]
        
        # Check file size based on type
        if file_type == 'image':
            if file.size > self.MAX_IMAGE_SIZE:
                return {'valid': False, 'error': f'Image files must be smaller than {self.MAX_IMAGE_SIZE // 1024 // 1024}MB'}
            if mime_type not in self.ALLOWED_IMAGE_TYPES:
                return {'valid': False, 'error': 'Invalid image format. Allowed: JPEG, PNG, GIF, WebP'}
                
        elif file_type == 'video':
            if file.size > self.MAX_VIDEO_SIZE:
                return {'valid': False, 'error': f'Video files must be smaller than {self.MAX_VIDEO_SIZE // 1024 // 1024}MB'}
            if mime_type not in self.ALLOWED_VIDEO_TYPES:
                return {'valid': False, 'error': 'Invalid video format. Allowed: MP4, WebM, OGG, AVI, MOV'}
                
        elif file_type == 'audio':
            if file.size > self.MAX_AUDIO_SIZE:
                return {'valid': False, 'error': f'Audio files must be smaller than {self.MAX_AUDIO_SIZE // 1024 // 1024}MB'}
            if mime_type not in self.ALLOWED_AUDIO_TYPES:
                return {'valid': False, 'error': 'Invalid audio format. Allowed: MP3, WAV, OGG, M4A, WebM'}
                
        elif file_type == 'document':
            if file.size > self.MAX_DOCUMENT_SIZE:
                return {'valid': False, 'error': f'Document files must be smaller than {self.MAX_DOCUMENT_SIZE // 1024 // 1024}MB'}
            if mime_type not in self.ALLOWED_DOCUMENT_TYPES:
                return {'valid': False, 'error': 'Invalid document format. Allowed: PDF, DOC, DOCX, XLS, XLSX, TXT, CSV'}
        
        return {'valid': True}
    
    def _get_upload_path(self, file_type, filename):
        """Get the upload path based on file type"""
        date_path = timezone.now().strftime('%Y/%m/%d')
        return f"chat/{file_type}s/{date_path}/{filename}"
    
    def _process_file_metadata(self, file, file_type, file_path):
        """Process and extract metadata from uploaded file"""
        metadata = {}
        
        try:
            if file_type == 'image':
                metadata.update(self._process_image_metadata(file_path))
            elif file_type == 'video':
                metadata.update(self._process_video_metadata(file_path))
            elif file_type == 'audio':
                metadata.update(self._process_audio_metadata(file_path))
        except Exception as e:
            print(f"Error processing {file_type} metadata: {e}")
        
        return metadata
    
    def _process_image_metadata(self, file_path):
        """Extract image metadata"""
        try:
            full_path = default_storage.path(file_path)
            with Image.open(full_path) as img:
                return {
                    'dimensions': {
                        'width': img.width,
                        'height': img.height
                    }
                }
        except Exception:
            return {}
    
    def _process_video_metadata(self, file_path):
        """Extract video metadata (requires ffmpeg-python)"""
        # This is a basic implementation
        # For production, consider using ffmpeg-python to extract duration, dimensions, etc.
        try:
            # You would use ffmpeg-python here to extract metadata
            # For now, returning empty dict
            return {
                'duration': None,  # Duration in seconds
                'dimensions': None,  # {'width': 1920, 'height': 1080}
                'thumbnail_url': None  # Generated thumbnail URL
            }
        except Exception:
            return {}
    
    def _process_audio_metadata(self, file_path):
        """Extract audio metadata"""
        # This is a basic implementation
        # For production, consider using mutagen or similar library
        try:
            return {
                'duration': None  # Duration in seconds
            }
        except Exception:
            return {}


class VoiceMessageUploadView(APIView):
    """
    Special endpoint for voice message uploads with real-time processing
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    MAX_VOICE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_VOICE_TYPES = ['audio/webm', 'audio/ogg', 'audio/wav', 'audio/m4a', 'audio/mpeg']
    
    def post(self, request):
        """Upload a voice message"""
        try:
            if 'voice' not in request.FILES:
                return Response({
                    'success': False,
                    'error': 'No voice file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            voice_file = request.FILES['voice']
            
            # Validate voice file
            if voice_file.size > self.MAX_VOICE_SIZE:
                return Response({
                    'success': False,
                    'error': f'Voice messages must be smaller than {self.MAX_VOICE_SIZE // 1024 // 1024}MB'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            mime_type = voice_file.content_type or mimetypes.guess_type(voice_file.name)[0]
            if mime_type not in self.ALLOWED_VOICE_TYPES:
                return Response({
                    'success': False,
                    'error': 'Invalid voice format. Allowed: WebM, OGG, WAV, M4A, MP3'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate unique filename
            file_extension = os.path.splitext(voice_file.name)[1] or '.webm'
            unique_filename = f"voice_{uuid.uuid4().hex}{file_extension}"
            
            # Upload path
            date_path = timezone.now().strftime('%Y/%m/%d')
            upload_path = f"chat/voice/{date_path}/{unique_filename}"
            
            # Save file
            file_path = default_storage.save(upload_path, ContentFile(voice_file.read()))
            file_url = default_storage.url(file_path)
            
            # Try to extract duration (basic implementation)
            duration = self._extract_voice_duration(file_path)
            
            return Response({
                'success': True,
                'file_data': {
                    'file_url': file_url,
                    'file_name': f"Voice message {timezone.now().strftime('%H:%M')}",
                    'file_size': voice_file.size,
                    'file_type': mime_type,
                    'message_type': 'audio',
                    'duration': duration
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Voice upload failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _extract_voice_duration(self, file_path):
        """Extract voice message duration"""
        try:
            # This is a placeholder - in production you'd use a library like mutagen
            # or subprocess with ffprobe to get the actual duration
            return None  # Duration in seconds
        except Exception:
            return None


class ImagePreviewView(APIView):
    """
    Generate thumbnail/preview for images
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Generate image preview/thumbnail"""
        try:
            image_url = request.data.get('image_url')
            if not image_url:
                return Response({
                    'success': False,
                    'error': 'image_url is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract file path from URL
            file_path = image_url.replace(settings.MEDIA_URL, '')
            full_path = default_storage.path(file_path)
            
            if not default_storage.exists(file_path):
                return Response({
                    'success': False,
                    'error': 'Image file not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Generate thumbnail
            thumbnail_path = self._generate_thumbnail(file_path, full_path)
            
            if thumbnail_path:
                thumbnail_url = default_storage.url(thumbnail_path)
                return Response({
                    'success': True,
                    'thumbnail_url': thumbnail_url
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to generate thumbnail'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Thumbnail generation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_thumbnail(self, file_path, full_path, size=(300, 300)):
        """Generate thumbnail for image"""
        try:
            # Create thumbnail path
            path_parts = file_path.split('/')
            filename = path_parts[-1]
            name, ext = os.path.splitext(filename)
            thumbnail_filename = f"{name}_thumb{ext}"
            thumbnail_path = '/'.join(path_parts[:-1] + [thumbnail_filename])
            
            # Check if thumbnail already exists
            if default_storage.exists(thumbnail_path):
                return thumbnail_path
            
            # Generate thumbnail
            with Image.open(full_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                thumbnail_full_path = default_storage.path(thumbnail_path)
                os.makedirs(os.path.dirname(thumbnail_full_path), exist_ok=True)
                img.save(thumbnail_full_path, optimize=True, quality=85)
                
                return thumbnail_path
                
        except Exception as e:
            print(f"Thumbnail generation error: {e}")
            return None