"""
Handle the signal problem with recipe!
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.models import Recipe, UserFollowing

import logging

logger = logging.getLogger(__name__)

def get_user_following(user):
    """Get user following user list"""
    return [follow.user_id for follow in UserFollowing.objects.filter(following_user_id=user).prefetch_related('user_id').distinct()]


@receiver(post_save, sender=Recipe)
def create_recipe(sender, instance, created, **kwargs):
    """After user create the recipe, django channel will send notification to followers!"""
    if created:
        channel_layer = get_channel_layer()
        followers = get_user_following(instance.user)
        if followers is not None:
            for followee in followers:
                group_name = f'user_{followee.id}_follows'
                message = {'type':'send_notification', 'text':'The user you follow has publish new recipe!'}
                async_to_sync(channel_layer.group_send(
                    group_name,
                    message
                ))
        else:
            pass
    else:
        logger.info("Recipe not created!")

