from rest_framework import serializers

from base.serializers import BaseModelSerializer
from country.serializers import CountrySerializer, CountryOfficialSerializer
from system.models import Log


class LogSerializer(BaseModelSerializer):
    class Meta:
        model = Log
        fields = ['category', 'content', 'created_at']


class CharaProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    country = CountrySerializer()
    official = CountryOfficialSerializer(fields=['title'])


class ChatMessageSerializer(serializers.Serializer):
    channel = serializers.SerializerMethodField()
    content = serializers.CharField()
    type = serializers.SerializerMethodField()
    sender = CharaProfileSerializer()
    created_at = serializers.DateTimeField()

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


class PrivateChatMessageSerializer(ChatMessageSerializer):
    receiver = CharaProfileSerializer()
    is_system_generated = serializers.BooleanField()

    class Meta:
        channel = 'private'
