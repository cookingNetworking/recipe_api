import boto3
import datetime
import django_redis
import os
from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from botocore.signers import CloudFrontSigner

from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.conf import settings
from django.db.models import F

from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination

from core import models
from .redis_set import RedisHandler


redis_client1 = django_redis.get_redis_connection("default")

def rsa_signer(message):
    """Hash the private key for singned cloudfront url!!"""
    private_key = serialization.load_pem_private_key(
        settings.AWS_CLOUDFRONT_KEY,
        password = None,
        backend=default_backend()
    )
    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())

def create_signed_url(image_path, expired_time):
    """
    Create signed url !
    Exprired time should be minutes!
    """
    url = f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/{image_path}'
    expired_time = datetime.datetime.utcnow() + datetime.timedelta(minute=30)
    key_id = settings.AWS_CLOUDFRONT_KEY_ID
    cloudfront_signer = CloudFrontSigner(key_id, rsa_signer)
    signed_url = cloudfront_signer.generate_presigned_url(
                                                        url,
                                                        date_less_than=expired_time)
    return signed_url

def conditional_csrf_decorator(views):
    """Csrf protect would set up by develop environments!"""
    if os.environ.get('DEV_ENV') == 'true':
        print('csrf_exempt')
        return csrf_exempt(views)
    else:
        print('csrf_protect')
        return csrf_protect(views)

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
        if os.environ.get('DEV_ENV') != 'true': # If is in develop, not use csrftoken
            if request.method not in ['GET', 'HEAD', 'OPTIONS', 'TRASE']:
                return csrf_protect(super().dispatch)(request, *args, **kwargs)
            else:
                return super().dispatch(request, *args, **kwargs)
        return csrf_exempt(super().dispatch)(request, *args, **kwargs)



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

