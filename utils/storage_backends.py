from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings




class StaticStorage(S3Boto3Storage):
    location = "static"
    default_acl = None

class MediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = None




import boto3
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
