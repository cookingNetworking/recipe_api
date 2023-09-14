"""
Replicated function.
"""

from celery import shared_task
from django.contrib.auth import get_user_model


@shared_task
def delete_unactivate_user(user_email):
    user = get_user_model().objects.filter(email=user_email).first()
    if not user.is_actived:
        user.delete()
