from django.db.models import F
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from chara.models import Chara, CharaIntroduction


class CharaIntroductionSerializer(BaseModelSerializer):
    class Meta:
        model = CharaIntroduction
        fields = ['content']


class SendMoneySerializer(BaseSerializer):
    gold = serializers.IntegerField(min_value=1)
    receiver_name = serializers.CharField()

    def save(self):
        chara = self.instance
        receiver = self.validated_data['receiver']
        gold = self.validated_data['gold']

        chara.gold -= gold
        chara.save()
        Chara.objects.filter(id=receiver.id).update(gold=F('gold') + gold)

    def validate_gold(self, value):
        if value > self.instance.gold:
            raise serializers.ValidationError("你的金錢不足")
        return value

    def validate(self, data):
        receiver = Chara.objects.filter(name=data['receiver_name']).first()
        if receiver is None:
            raise serializers.ValidationError("收款人不存在")

        data['receiver'] = receiver

        return data
