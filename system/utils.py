from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync

from chara.models import Chara
from system.models import Log, PrivateChatMessage


def get_chara_profile_sync(chara_id):
    profile = Chara.objects.values('id', 'name', 'country__name', 'official__title').get(id=chara_id)
    profile['country'] = {'name': profile.pop('country__name')} if profile['country__name'] else None
    profile['official'] = {'title': profile.pop('official__title')} if profile['official__title'] else None
    return profile


get_chara_profile = database_sync_to_async(get_chara_profile_sync)


def push_log(category, content):
    log = Log.objects.create(category=category, content=content)
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        'log',
        {'type': 'log_message', 'category': category, 'content': content, 'created_at': log.created_at.isoformat()}
    )


def send_private_message_by_system(sender, receiver, content):
    message = PrivateChatMessage.objects.create(
        sender=sender, receiver=receiver, content=content, is_system_generated=True)
    data = {'type': 'chat_message', 'channel': 'private',
            'content': content, 'created_at': message.created_at.isoformat()}
    data['sender'] = get_chara_profile_sync(sender.id)
    data['receiver'] = get_chara_profile_sync(receiver.id)

    layer = get_channel_layer()
    for chara in [sender, receiver]:
        async_to_sync(layer.group_send)(f'private_{chara.id}', data)
