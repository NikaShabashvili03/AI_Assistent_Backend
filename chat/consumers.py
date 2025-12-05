import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ConversationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        print("Connecting user:", self.user)

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4003)
            return

        self.room_group_name = f"conversations_{self.user.id}"

        if not self.channel_layer:
            await self.close(code=1011)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name") and self.channel_layer:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_conversation_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "conversation_update",
            "data": event["data"]
        }))

    # async def send_conversation_delete(self, event):
    #     await self.send(text_data=json.dumps({
    #         "type": "conversation_delete",
    #         "data": event["data"]
    #     }))



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        
        print("Connecting to chat, user:", self.user)

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4003)
            return

        print("kwargs:", self.scope['url_route']['kwargs'])

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f"chat_{self.conversation_id}"

        print("Checking membership for user:", self.user, "in conversation:", self.conversation_id)
        from chat.models import ConversationUsers

        is_member = await database_sync_to_async(
            ConversationUsers.objects.filter(
                conversation_id=self.conversation_id,
                user=self.user
            ).exists
        )()

        print("Is member:", is_member)
        if not is_member:
            await self.close(code=4008) 
            return

        print("Adding to group:", self.room_group_name)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception:
            pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": self.user.id,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))