from rest_framework import serializers

from country.serializers import CountrySerializer, CountryOfficialSerializer


class CharaProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    country = CountrySerializer(fields=['name'])
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

    class Meta:
        channel = 'private'
