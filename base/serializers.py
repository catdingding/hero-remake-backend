from rest_framework import serializers
from chara.models import Chara


class ContextMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = self.context.get('request')
        if self.request:
            self.user = self.request.user


class BaseSerializer(ContextMixin, serializers.Serializer):
    pass


class BaseModelSerializer(ContextMixin, serializers.ModelSerializer):
    pass