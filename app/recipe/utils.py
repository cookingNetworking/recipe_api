import boto3

from botocore.config import Config

from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.db.models import F

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination

from core import models
from .redis_set import RedisHandler

import django_redis

redis_client1 = django_redis.get_redis_connection("default")


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
    recipe_redis_handler = RedisHandler(redis_client1)
    if isinstance(obj, models.Recipe):
        save, created = models.Save.objects.get_or_create(user=user, recipe=obj)
        if created:
            obj.save_count = F('save_count') + 1
            obj.save(update_fields=['save_count'])
            recipe_redis_handler.increase_recipe_view(hkey_name="save_count", recipe_id=obj.id)
            return Response({'message':'User save the recipe!'}, status=status.HTTP_200_OK)
        elif save:
            obj.save_count =F('save_count') - 1
            obj.save(update_fields=['save_count'])
            save.delete()
            recipe_redis_handler.increase_recipe_view(hkey_name="save_count", recipe_id=obj.id, increment_value= -1)
            return Response({'message':'User unsaved the recipe !'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unknow error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif isinstance(obj, models.Tag):
        save, created = models.Save.objects.get_or_create(user=user, tag=obj)
        if created:
            obj.save_count =F('save_count') + 1
            obj.save(update_fields=['save_count'])
            return Response({'message':'User save the tag!'}, status=status.HTTP_200_OK)
        elif save:
            obj.save_count =F('save_count') - 1
            obj.save(update_fields=['save_count'])
            save.delete()
            return Response({'message':'User unsaved the tag !'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unknow error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif isinstance(obj, models.Ingredient):
        save, created = models.Save.objects.get_or_create(user=user, ingredient=obj)
        if created:
            obj.save_count =F('save_count') + 1
            obj.save(update_fields=['save_count'])
            return Response({'message':'User save the ingredient!'}, status=status.HTTP_200_OK)
        elif save:
            obj.save_count =F('save_count') - 1
            obj.save(update_fields=['save_count'])
            save.delete()
            return Response({'message':'User unsaved the ingredient !'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unknow error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'error': 'No valid object found'}, status=status.HTTP_400_BAD_REQUEST)


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

class CustomPagination(PageNumberPagination):
    """Customerized the page numer."""
    page_size = 30

