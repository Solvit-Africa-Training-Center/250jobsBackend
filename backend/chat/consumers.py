import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import now
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from .models import Room, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"chat_{self.room_id}"
        self.user = self.scope.get("user", None)

        if not self.user or isinstance(self.user, AnonymousUser):
            await self.close(code=4401)
            return
        
        # Ensure the user is a participant of the room
        is_member = await self._user_in_room(self.user.id, int(self.room_id))
        if not is_member:
            await self.close(code=4403)
            return
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        
        try:
            data = json.loads(text_data)
            content = data.get("content", "").strip()
        except Exception:
            content =""
        
        if not content:
            return
        
        message = await self.create_message(self.user.id, int(self.room_id), content)


        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message": {
                    "id": message["id"],
                    "room": message["room"],
                    "sender": message["sender"],
                    "content": message["content"],
                    "timestamp": message["timestamp"],
                    "read": message["read"],
                },
            },
        )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
    
    @database_sync_to_async
    def _user_in_room(self, user_id, room_id):
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return False
        return room.participants.filter(id=user_id).exists()
    
    @database_sync_to_async
    def create_message(self, sender_id, room_id, content):
        sender = User.objects.get(id=sender_id)
        room = Room.objects.get(id=room_id)
        msg = Message.objects.create(room=room, sender=sender, content=content)
        return {
            "id": msg.id,
            "room": room.id,
            "sender": {
                "id": sender.id,
                "username": sender.username,
                "email": sender.email,
                "role": getattr(sender, "role", None),
            },
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "read": msg.read,
        }
