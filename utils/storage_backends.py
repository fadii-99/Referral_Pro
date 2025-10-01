from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings




class StaticStorage(S3Boto3Storage):
    location = "static"
    default_acl = None

class MediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = None




import boto3
import uuid
import mimetypes
from django.conf import settings

def generate_presigned_url(key, expires_in=3600):
    """
    Generate a presigned URL for an S3 object.
    :param key: Path in the bucket, e.g. "media/user_profiles/East_Europe_Trip_062d.jpeg"
    :param expires_in: Expiration time in seconds (default 1 hour)
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=expires_in,
    )

def upload_file_to_s3(file, folder='chat_files'):
    """
    Upload a file to S3 and return file details.
    :param file: The file object from request.FILES
    :param folder: The folder in S3 bucket to store the file
    :return: Dict with file_url, file_name, file_size, file_type
    """
    # Generate a unique filename
    file_ext = file.name.split('.')[-1] if '.' in file.name else ''
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else f"{uuid.uuid4().hex}"
    
    # Define the S3 key (path)
    key = f"{folder}/{unique_filename}"
    
    # Get or guess content type
    content_type = getattr(file, 'content_type', None)
    if not content_type:
        content_type = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
    
    # Upload to S3
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    
    s3_client.upload_fileobj(
        file,
        settings.AWS_STORAGE_BUCKET_NAME,
        key,
        ExtraArgs={
            'ContentType': content_type,
        }
    )
    
    # Generate URL
    file_url = generate_presigned_url(key)
    
    return {
        'file_url': file_url,
        'file_name': file.name,
        'file_size': file.size,
        'file_type': content_type,
        's3_key': key
    }
