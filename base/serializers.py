from django.utils.module_loading import import_string
from rest_framework import serializers
from rest_flex_fields.serializers import FlexFieldsSerializerMixin
from chara.models import Chara


class ContextMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = self.context.get('request')
        if self.request:
            self.user = self.request.user

            if hasattr(self.request, 'chara'):
                self.chara = self.request.chara
            if hasattr(self.request, 'country'):
                self.country = self.request.country
            if hasattr(self.request, 'team'):
                self.team = self.request.team


class BaseSerializer(ContextMixin, FlexFieldsSerializerMixin, serializers.Serializer):
    pass


class BaseModelSerializer(ContextMixin, FlexFieldsSerializerMixin, serializers.ModelSerializer):
    pass
