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
    return [follow.id for follow in UserFollowing.objects.filter(following_user_id=user).prefetch_related('user_id').distinct()]


@receiver(post_save, sender=Recipe)
def create_recipe(sender, instance, created, **kwargs):
    """After user create the recipe, django channel will send notification to followers!"""
    try:
        if created:
            channel_layer = get_channel_layer()
            # Get user followers id and set in to list
            followers_id = get_user_following(instance.user)
            group_name = f'user_{instance.user.id}_follows'
            event = {
                        'type':'test_recipe_create',
                        'text':f'The user you follow {instance.user.username} has publish new recipe!',
                        'user_id':followers_id,
                    }
            async_to_sync(channel_layer.group_send)(
                group_name,
                event
                )
            logger.info("Recipe created!")
        else:
            logger.info("Recipe not created!")
    except Exception as e:
        logger.error(e)
        logger.info("Recipe not created!")
