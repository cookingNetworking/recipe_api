"""
Logic for real time notification with websocket!!!
"""

import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    """Connect and disconnect websocket!"""
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            followings  = await self.get_user_following(user=user)
            for followee in followings:
                group_name = f'user_{followee.id}_follows'
                await self.channel_layer.group_add(
                    group_name,
                    self.channel_name
                )
            await self.accept()
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    @database_sync_to_async
    def get_user_following(self, user):
        """Get user following user list"""
        from core.models import UserFollowing
        return [follow.following_user_id for follow in UserFollowing.objects.filter(user_id=user)]

