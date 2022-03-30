from rest_framework import serializers
import serpy

from base.serializers import BaseModelSerializer, SerpyModelSerializer, DateTimeField
from asset.serializers import ImageSerializer
from chara.serializers import CharaTitleSerializer, CharaCustomTitleSerializer
from country.serializers import CountrySerializer, CountryOfficialSerializer
from system.models import Log, ChangeLog


class ChangeLogSerializer(SerpyModelSerializer):
    class Meta:
        model = ChangeLog
        fields = ['id', 'category', 'content', 'note', 'time']


class LogSerializer(SerpyModelSerializer):
    class Meta:
        model = Log
        fields = ['category', 'content', 'created_at']


class CharaProfileSerializer(SerpyModelSerializer):
    id = serpy.Field()
    name = serpy.Field()
    avatar_version = serpy.Field()
    country = CountrySerializer()
    official = CountryOfficialSerializer(fields=['title'])
    title = CharaTitleSerializer(fields=['type'])
    custom_title = CharaCustomTitleSerializer()


class ChatMessageSerializer(SerpyModelSerializer):
    channel = serpy.MethodField()
    content = serpy.Field()
    type = serpy.MethodField()
    sender = CharaProfileSerializer()
    created_at = DateTimeField()

    def get_channel(self, obj):
        return self.Meta.channel

    def get_type(self, obj):
        return "chat_message"


class PublicChatMessageSerializer(ChatMessageSerializer):
    class Meta:
        channel = 'public'


class CountryChatMessageSerializer(ChatMessageSerializer):
    class Meta:
        channel = 'country'


class TeamChatMessageSerializer(ChatMessageSerializer):
    class Meta:
        channel = 'team'


class PrivateChatMessageSerializer(ChatMessageSerializer):
    receiver = CharaProfileSerializer()
    is_system_generated = serpy.Field()

    class Meta:
        channel = 'private'


class SystemChatMessageSerializer(SerpyModelSerializer):
    channel = serpy.MethodField()
    content = serpy.Field()
    type = serpy.MethodField()
    sender_name = serpy.Field()
    avatar = ImageSerializer(fields=['path'])
    created_at = DateTimeField()

    def get_channel(self, obj):
        return "system"

    def get_type(self, obj):
        return "chat_message"
