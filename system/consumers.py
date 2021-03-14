from datetime import datetime

from django.db.models import Q
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from chara.models import Chara
from system.models import PublicChatMessage, CountryChatMessage, PrivateChatMessage
from system.serializers import PublicChatMessageSerializer, CountryChatMessageSerializer, PrivateChatMessageSerializer


@database_sync_to_async
def get_chara_profile(chara_id):
    profile = Chara.objects.values('id', 'name', 'country__name', 'official__title').get(id=chara_id)
    profile['country'] = {'name': profile.pop('country__name')}
    profile['official'] = {'title': profile.pop('official__title')}
    return profile


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        for group in self.scope['group_mapping'].values():
            await self.channel_layer.group_add(group, self.channel_name)

        await self.accept()
        await self.load_messages()

    async def disconnect(self, close_code):
        for group in self.scope['group_mapping'].values():
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, data):
        data['content'] = data['content'][:100]
        await self.save_message(data)

        channel = data['channel']
        receiver = data.pop('receiver', None)

        data['type'] = 'chat_message'
        data['sender'] = await get_chara_profile(self.scope['chara_id'])
        data['created_at'] = datetime.now().isoformat() + 'Z'
        if receiver is not None:
            data['receiver'] = await get_chara_profile(receiver)

        if channel == 'private':
            await self.send_json(data)
            await self.channel_layer.group_send(f'private_{receiver}', data)
        else:
            await self.channel_layer.group_send(self.scope['group_mapping'][channel], data)

    @database_sync_to_async
    def save_message(self, data):
        if data['channel'] == 'public':
            PublicChatMessage.objects.create(sender_id=self.scope['chara_id'], content=data['content'])
        elif data['channel'] == 'country':
            CountryChatMessage.objects.create(
                country_id=self.scope['country_id'], sender_id=self.scope['chara_id'], content=data['content']
            )
        elif data['channel'] == 'private':
            PrivateChatMessage.objects.create(
                sender_id=self.scope['chara_id'], receiver_id=data['receiver'], content=data['content']
            )

    async def load_messages(self):
        messages = await self.get_public_chat_messages() + await self.get_country_chat_messages() + await self.get_private_chat_messages()
        messages.sort(key=lambda x: x['created_at'])
        for message in messages:
            await self.send_json(message)

    @database_sync_to_async
    def get_public_chat_messages(self):
        queryset = PublicChatMessage.objects.order_by('-created_at')[:10]
        return PublicChatMessageSerializer(queryset, many=True).data[::-1]

    @database_sync_to_async
    def get_country_chat_messages(self):
        queryset = CountryChatMessage.objects.filter(country=self.scope['country_id']).order_by('-created_at')[:10]
        return CountryChatMessageSerializer(queryset, many=True).data[::-1]

    @database_sync_to_async
    def get_private_chat_messages(self):
        queryset = PrivateChatMessage.objects.filter(
            Q(sender=self.scope['chara_id']) | Q(receiver=self.scope['chara_id'])
        ).order_by('-created_at')[:10]
        return PrivateChatMessageSerializer(queryset, many=True).data[::-1]

    async def chat_message(self, event):
        await self.send_json(event)
