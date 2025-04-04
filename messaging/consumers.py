import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Conversation

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        if self.scope['user'].is_anonymous or self.scope['user'] not in Conversation.objects.get(id=self.conversation_id).participants.all():
            await self.close()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        typing = data.get('typing', False)
        if typing:
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'typing',
                'sender': self.scope['user'].username
            })
        elif message and message.strip():
            msg = Message.objects.create(
                conversation_id=self.conversation_id,
                sender=self.scope['user'],
                content=message
            )
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat_message',
                'message': message,
                'sender': self.scope['user'].username,
                'timestamp': msg.timestamp.isoformat(),
            })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
        }))

    async def typing(self, event):
        await self.send(text_data=json.dumps({
            'typing': True,
            'sender': event['sender']
        }))