from rest_framework import serializers


class ContextMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = self.context.get('request')
        if self.request:
            self.user = self.request.user


class CharaCheckMixin:
    def validate_chara(self, value):
        if not self.user.charas.filter(id=value).exists():
            raise serializers.ValidationError("角色錯誤")
        return value


class BaseSerializer(ContextMixin, serializers.Serializer):
    pass


class BaseModelSerializer(ContextMixin, serializers.ModelSerializer):
    pass
