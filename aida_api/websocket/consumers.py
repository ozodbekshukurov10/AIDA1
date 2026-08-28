"""
AIDA Enterprise API — WebSocket Consumers

Real-time communication uchun WebSocket consumer'lari.
"""
from __future__ import annotations
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Real-time chat consumer.
    
    ws://api.aida.ai/ws/v1/chat/{chat_id}/
    """

    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.room_group_name = f"chat_{self.chat_id}"

        # Room group ga qo'shilish
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "message")

        if message_type == "message":
            # Xabarni room group ga yuborish
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": data.get("message", ""),
                    "sender": data.get("sender", "user"),
                },
            )
        elif message_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "sender": data.get("sender", "user"),
                },
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "sender": event["sender"],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "sender": event["sender"],
        }))


class AgentConsumer(AsyncWebsocketConsumer):
    """
    Agent events consumer.
    
    ws://api.aida.ai/ws/v1/agents/{agent_id}/
    """

    async def connect(self):
        self.agent_id = self.scope["url_route"]["kwargs"]["agent_id"]
        self.group_name = f"agent_{self.agent_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connected",
            "agent_id": self.agent_id,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Agent ga command yuborish
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "agent_event",
                "event": data.get("event", "unknown"),
                "data": data.get("data", {}),
            },
        )

    async def agent_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "event",
            "event": event["event"],
            "data": event["data"],
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Notification consumer — foydalanuvchi xabarnomalar.
    
    ws://api.aida.ai/ws/v1/notifications/
    """

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass  # Faqat serverdan client ga

    async def notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "title": event.get("title", ""),
            "message": event.get("message", ""),
            "level": event.get("level", "info"),
        }))
