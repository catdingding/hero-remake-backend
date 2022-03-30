from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync

from asset.models import Image
from chara.models import Chara
from system.models import Log, PrivateChatMessage, SystemChatMessage


def get_chara_profile_sync(chara_id):
    profile = Chara.objects.values(
        'id', 'avatar_version', 'name', 'country__name', 'official__title', 'title__type__name',
        'custom_title__name', 'custom_title__color', 'custom_title__due_time'
    ).get(id=chara_id)
    profile['country'] = {'name': profile.pop('country__name')} if profile['country__name'] else None
    profile['official'] = {'title': profile.pop('official__title')} if profile['official__title'] else None
    profile['title'] = {'type': {'name': profile.pop('title__type__name')}} if profile['title__type__name'] else None
    profile['custom_title'] = {x: profile.pop(f'custom_title__{x}') for x in ['name', 'color', 'due_time']}
    profile['custom_title']['due_time'] = profile['custom_title']['due_time'].isoformat()
    return profile


get_chara_profile = database_sync_to_async(get_chara_profile_sync)


def push_log(category, content):
    log = Log.objects.create(category=category, content=content)
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        'log',
        {'type': 'log_message', 'category': category, 'content': content, 'created_at': log.created_at.isoformat()}
    )


def send_private_message_by_system(sender_id, receiver_id, content):
    message = PrivateChatMessage.objects.create(
        sender_id=sender_id, receiver_id=receiver_id, content=content, is_system_generated=True)
    data = {'type': 'chat_message', 'channel': 'private', 'is_system_generated': True,
            'content': content, 'created_at': message.created_at.isoformat()}
    data['sender'] = get_chara_profile_sync(sender_id)
    data['receiver'] = get_chara_profile_sync(receiver_id)

    layer = get_channel_layer()
    for chara_id in [sender_id, receiver_id]:
        async_to_sync(layer.group_send)(f'private_{chara_id}', data)


def send_system_message(sender_name, avatar_id, content):
    message = SystemChatMessage.objects.create(sender_name=sender_name, avatar_id=avatar_id, content=content)
    data = {
        'type': 'chat_message', 'channel': 'system', 'sender_name': sender_name,
        'content': content, 'created_at': message.created_at.isoformat()
    }
    data['avatar'] = {'path': Image.objects.get(id=avatar_id).path}

    layer = get_channel_layer()
    async_to_sync(layer.group_send)(f'public', data)


def send_refresh_chara_profile_signal(chara_id):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(f'private_{chara_id}', {'type': 'refresh_chara_profile'})


def send_info_message(chara_id, type, content):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(f'private_{chara_id}', {
        'type': 'info_message', 'content': content, 'message_type': type})
