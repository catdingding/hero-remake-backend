import json
from datetime import datetime

from django.db.models import Q
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async, SyncToAsync

from system.models import PublicChatMessage, CountryChatMessage, TeamChatMessage, PrivateChatMessage, SystemChatMessage
from system.serializers import (
    PublicChatMessageSerializer, CountryChatMessageSerializer, TeamChatMessageSerializer,
    PrivateChatMessageSerializer, SystemChatMessageSerializer
)
from system.utils import get_chara_profile, send_system_message
from system.chat_utils import system_chan_reply


class MessageConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('log', self.channel_name)
        for group in self.scope['group_mapping'].values():
            await self.channel_layer.group_add(group, self.channel_name)

        await self.accept()
        await self.load_messages()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('log', self.channel_name)
        for group in self.scope['group_mapping'].values():
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, data):
        if data['type'] == 'ping':
            await self.send_json({'type': 'pong'})
        elif data['type'] == 'chat_message':
            data['content'] = data['content'][:100].strip()
            await self.save_message(data)

            channel = data['channel']
            receiver = data.pop('receiver', None)

            data['sender'] = await get_chara_profile(self.scope['chara_id'])
            data['created_at'] = datetime.now().isoformat() + 'Z'
            if receiver is not None:
                data['receiver'] = await get_chara_profile(receiver)

            if channel == 'private' and receiver != self.scope['chara_id']:
                await self.channel_layer.group_send(f'private_{receiver}', data)
            await self.channel_layer.group_send(self.scope['group_mapping'][channel], data)

            if channel == 'public' and data['content'][:4] == '@系統醬':
                message = await system_chan_reply(data['content'][4:], data['sender'])
                await SyncToAsync(send_system_message)("系統醬", 1, message)

    @database_sync_to_async
    def save_message(self, data):
        if data['channel'] == 'public':
            PublicChatMessage.objects.create(sender_id=self.scope['chara_id'], content=data['content'])
        elif data['channel'] == 'country':
            CountryChatMessage.objects.create(
                country_id=self.scope['country_id'], sender_id=self.scope['chara_id'], content=data['content']
            )
        elif data['channel'] == 'team':
            TeamChatMessage.objects.create(
                team_id=self.scope['team_id'], sender_id=self.scope['chara_id'], content=data['content']
            )
        elif data['channel'] == 'private':
            PrivateChatMessage.objects.create(
                sender_id=self.scope['chara_id'], receiver_id=data['receiver'], content=data['content']
            )

    async def load_messages(self):
        messages = (
            await self.get_public_chat_messages() + await self.get_country_chat_messages() +
            await self.get_team_chat_messages() + await self.get_private_chat_messages() +
            await self.get_system_chat_messages()
        )
        messages.sort(key=lambda x: x['created_at'])
        for message in messages:
            message['is_init'] = True
            await self.send_json(message)

    def select_chara_field(self, chara_field, queryset):
        return queryset.select_related(
            f'{chara_field}__country', f'{chara_field}__official',
            f'{chara_field}__title__type', f'{chara_field}__custom_title',
        )

    @database_sync_to_async
    def get_public_chat_messages(self):
        queryset = PublicChatMessage.objects.order_by('-created_at')[:10]
        queryset = self.select_chara_field('sender', queryset)
        return PublicChatMessageSerializer(queryset, many=True).data[::-1]

    @database_sync_to_async
    def get_country_chat_messages(self):
        queryset = CountryChatMessage.objects.filter(country=self.scope['country_id']).order_by('-created_at')[:10]
        queryset = self.select_chara_field('sender', queryset)
        return CountryChatMessageSerializer(queryset, many=True).data[::-1]

    @database_sync_to_async
    def get_team_chat_messages(self):
        queryset = TeamChatMessage.objects.filter(team=self.scope['team_id']).order_by('-created_at')[:10]
        queryset = self.select_chara_field('sender', queryset)
        return TeamChatMessageSerializer(queryset, many=True).data[::-1]

    @database_sync_to_async
    def get_private_chat_messages(self):
        queryset = PrivateChatMessage.objects.filter(
            Q(sender=self.scope['chara_id']) | Q(receiver=self.scope['chara_id'])
        ).order_by('-created_at')[:10]
        queryset = self.select_chara_field('sender', queryset)
        queryset = self.select_chara_field('receiver', queryset)
        return PrivateChatMessageSerializer(queryset, many=True).data[::-1]

    @database_sync_to_async
    def get_system_chat_messages(self):
        queryset = SystemChatMessage.objects.order_by('-created_at')[:10]
        queryset = queryset.select_related('avatar')
        return SystemChatMessageSerializer(queryset, many=True).data[::-1]

    @classmethod
    async def encode_json(cls, content):
        return json.dumps(content, ensure_ascii=False)

    async def chat_message(self, event):
        await self.send_json(event)

    async def log_message(self, event):
        await self.send_json(event)

    async def info_message(self, event):
        await self.send_json(event)

    async def refresh_chara_profile(self, event):
        await self.send_json(event)
