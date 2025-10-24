import json
from channels.generic.websocket import AsyncWebsocketConsumer

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