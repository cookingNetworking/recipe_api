"""
Logic for real time notification with websocket!!!
"""

import json, logging

from django.template.loader import get_template
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class NotificationConsumer(WebsocketConsumer):
    """Connect and disconnect websocket!"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.groups = []

    def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            try:
                followings  = self.get_user_following(user=user)
                if followings is not None:
                    for followee in followings:
                        group_name = f'user_{followee.id}_follows'
                        self.groups.append(group_name)
                        async_to_sync(self.channel_layer.group_add)(
                            group_name,
                            self.channel_name
                        )
                logger.info("Websocket connect!!")
                self.accept()
            except Exception as e:
                logger.error("Error in connection %s", e)
        else:
            logger.info("Unauthenticated user attemptedto connect!!")

    def disconnect(self, close_code):
        if self.groups is None:
           self.close()
           pass
        for group_name in self.groups:
            async_to_sync(self.channel_layer.group_discard(
                group_name,
                self.channel_name
            ))
        self.close()
    def recipe_create(self, event):
        """Send message to websocket."""
        from .tasks import create_notification
        self.send(text_data=json.dumps({"message": event['text'],}))
        create_notification.apply_async(args=(event['user_id'], event['text']), countdown=0)

    def test_recipe_create(self, event):
        from .tasks import create_notification
        html = get_template('partial/notification.html').render(
            context = {'notification': event['text']}
        )
        print(event['user_id'])
        print(event['text'])
        self.send(text_data=html)
        create_notification.apply_async(args=(event['user_id'], event['text']), countdown=0)

    def get_user_following(self, user):
        """Get user following user list"""
        from core.models import UserFollowing
        return [follow.following_user_id for follow in UserFollowing.objects.filter(user_id=user).prefetch_related('following_user_id').distinct()]

