import boto3

from botocore.config import Config

from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.db.models import F

from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.viewsets import ModelViewSet
from .core import models


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

def saved_action(user, obj):
    """Funciton for save action."""
    save, created = models.Save.objects.get_or_create(user=user,obj=obj)
    if created:
        obj.save_count =F('save_count') + 1
        obj.save(update_fields=['save_count'])
        return Response({'message':'User save the recipe!'}, status=status.HTTP_200_OK)
    elif save:
        obj.save_count =F('save_count') - 1
        obj.save(update_fields=['save_count'])
        save.delete()
        return Response({'message':'User unsaved the recipe !'}, status=status.HTTP_200_OK)

class UnsafeMethodCSRFMixin(ModelViewSet):
    """Amixin that applies CSRF protection to unsafe HTTP methods (POST, PATCH, PUT, DELETE....)"""

    def dispatch(self, request, *args, **kwargs):
        if request.method not in ['GET', 'HEAD', 'OPTIONS', 'TRASE']:
            return csrf_protect(super().dispatch)(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)
    

class CustomSlugRelatedField(serializers.SlugRelatedField):
    """Custom slugrelated field that object does not exist return normal data!"""

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            error_detail = e.detail[0]
            if "does not exist" in error_detail:
                return data
            raise e  
        

