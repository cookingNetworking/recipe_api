"""
Replicated function.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework.response import Response

import os
import jwt

@shared_task
def delete_unactivate_user(user_email):
    user = get_user_model().objects.filter(email=user_email).first()
    if  user and not user.is_actived:
        user.delete()


def create_jwt(**payload):
    """Generate a jwt token ."""
    key = os.environ.get('secret_key')
    encoded = jwt.encode(payload, key, algorithm='HS256')
    return encoded


def sending_mail(toeamil, **content):
    """Function to send email . """    
    try:    
        send_mail(
        f"{content['subject']}",
        f"{content['message']}",
        "as2229181@gmail.com",
        [f"{toeamil}"],
        fail_silently=False,
        )
        return 
    except Exception as e:
        return e
        