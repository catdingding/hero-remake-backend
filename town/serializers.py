from django.db.models import Sum
from rest_framework import serializers

from base.serializers import BaseSerializer, BaseModelSerializer


class InnSleepSerializer(BaseSerializer):
    kind = serializers.CharField()

    def save(self):
        kind = self.validated_data['kind']

        if kind == 'room':
            self.chara.health = 100
            cost = self.chara.attributes.aggregate(value_sum=Sum('value'))['value_sum'] ** 2
        elif kind == 'stable':
            self.chara.health = max(50, self.chara.health)
            cost = 0

        self.chara.lose_gold(cost)
        self.chara.save()

        return {'display_message': f'花費了{cost}金錢住宿，健康度恢復了'}

    def validate_kind(self, kind):
        if kind not in ['room', 'stable']:
            serializers.ValidationError("類型不存在")
        return kind
