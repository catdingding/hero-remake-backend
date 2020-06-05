from rest_framework import serializers


class BaseSerializer(serializers.Serializer):
    pass


class BaseModelSerializer(serializers.ModelSerializer):
    pass
