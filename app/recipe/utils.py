import boto3

from botocore.config import Config

from django.views.decorators.csrf import csrf_protect
from django.conf import settings

from rest_framework.viewsets import ModelViewSet
def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object."""
    s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
							  region_name=settings.AWS_S3_REGION_NAME,
							  config=Config(signature_version='s3v4')
							  )

    response = s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name,
                                                        'Key': object_name},
                                                ExpiresIn=expiration)

    return response



class UnsafeMethodCSRFMixin(ModelViewSet):
    """Amixin that applies CSRF protection to unsafe HTTP methods (POST, PATCH, PUT, DELETE....)"""

    def dispatch(self, request, *args, **kwargs):
        if request.method not in ['GET', 'HEAD', 'OPTIONS', 'TRASE']:
            return csrf_protect(super().dispatch)