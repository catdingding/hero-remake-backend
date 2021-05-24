from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from system.models import Log


def push_log(category, content):
    log = Log.objects.create(category=category, content=content)
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        'log',
        {'type': 'log_message', 'category': category, 'content': content, 'created_at': log.created_at.isoformat()}
    )
