"""
Logic for real time notification with websocket!!!
"""

import json, logging
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    """Connect and disconnect websocket!"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.groups = []

    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            try:
                followings  = await self.get_user_following(user=user)
                if followings is not None:
                    for followee in followings:
                        group_name = f'user_{followee.id}_follows'
                        self.groups.append(group_name)
                        await self.channel_layer.group_add(
                            group_name,
                            self.channel_name
                        )
                await self.accept()        
            except Exception as e:
                logger.error("Error in connection %s", e)
        else:
            logger.info("Unauthenticated user attemptedto connect!!")
        

    async def create_recipe(self):
        user = self.scope["user"]
        if user.is_authenticated:
            followings  = await self.get_user_following(user=user)
            if followings is not None:
                for followee in followings:
                    group_name = f'user_{followee.id}_follows'
                    await self.channel_layer.group_send(
                        group_name,
                        {
                            'type': 'send_notification',
                            'message': {'text': f' The user you follow {user.username} has published new recipe! '}
                        }
                    )
            else:
                pass

    async def disconnect(self, close_code):
        if self.groups is None:
           self.close()
           pass
        for group_name in self.groups:
            await self.channel_layer.group_discard(
                group_name,
                self.channel_name
            )
        self.close()

    @database_sync_to_async
    def get_user_following(self, user):
        """Get user following user list"""
        from core.models import UserFollowing
        return [follow.user_id for follow in UserFollowing.objects.filter(following_user_id=user).prefetch_related('user_id').distinct()]

