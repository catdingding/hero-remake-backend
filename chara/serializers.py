from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from chara.models import CharaIntroduction


class CharaIntroductionSerializer(BaseModelSerializer):
    class Meta:
        model = CharaIntroduction
        fields = ['content']
