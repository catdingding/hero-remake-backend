import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from chara.models import Chara


@database_sync_to_async
def get_chara_profile(chara_id):
    return Chara.objects.values('id', 'name', 'country__name', 'official__title').get(id=chara_id)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        for group in self.scope['group_mapping'].values():
            await self.channel_layer.group_add(group, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        for group in self.scope['group_mapping'].values():
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, data):
        channel = data['channel']
        receiver = data.pop('receiver', None)

        data['type'] = 'chat_message'
        data['sender_profile'] = await get_chara_profile(self.scope['chara_id'])
        if receiver is not None:
            data['receiver_profile'] = await get_chara_profile(receiver)

        if channel == 'private':
            await self.send_json(data)
            await self.channel_layer.group_send(f'private_{receiver}', data)
        else:
            await self.channel_layer.group_send(self.scope['group_mapping'][channel], data)

    async def chat_message(self, event):
        await self.send_json(event)
