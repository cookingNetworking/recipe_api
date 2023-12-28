"""
Logic for real time notification with websocket!!!
"""

import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    """Connect and disconnect websocket!"""