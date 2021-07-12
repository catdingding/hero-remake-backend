from rest_framework_simplejwt.tokens import AccessToken
from jwt import decode as jwt_decode
from django.conf import settings
from channels.db import database_sync_to_async
from urllib.parse import parse_qs

from chara.models import Chara


@database_sync_to_async
def get_chara(**kwargs):
    return Chara.objects.get(**kwargs)


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode("utf-8"))

        token = query_string["token"][0]
        chara_id = int(query_string["chara"][0])

        user_id = AccessToken(token=token).get('user_id')
        chara = await get_chara(user=user_id, id=chara_id)

        scope['chara_id'] = chara.id
        scope['country_id'] = chara.country_id
        scope['team_id'] = chara.team_id
        scope['group_mapping'] = {
            'public': 'public',
            'country': f'country_{chara.country_id}',
            'team': f'team_{chara.team_id}',
            'private': f'private_{chara.id}'
        }

        return await self.app(scope, receive, send)
