from django.db.models import Sum
from rest_framework import serializers

from base.serializers import BaseSerializer, BaseModelSerializer
from town.models import Town

from system.utils import push_log


class TownSerializer(BaseModelSerializer):
    class Meta:
        model = Town
        fields = ['id', 'name']


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


class ChangeNameSerializer(BaseSerializer):
    kind = serializers.CharField()
    name = serializers.CharField()

    def save(self):
        kind = self.validated_data['kind']
        name = self.validated_data['name']

        if kind == 'chara':
            orig_name = self.chara.name
            self.chara.name = name
            message = f"{orig_name}改名為{name}"
        elif kind in ['weapon', 'armor', 'jewelry', 'pet']:
            equipment = self.chara.slots.get(type__en_name=kind).item.equipment
            orig_name = equipment.custom_name
            equipment.custom_name = name
            equipment.save()
            message = f"{self.chara.name}的{orig_name}改名為{name}"

        self.chara.lose_gold(100000000)
        self.chara.save()

        push_log("改名", message)
        return {'display_message': message}

    def validate_kind(self, kind):
        if kind == 'chara':
            pass
        elif kind in ['weapon', 'armor', 'jewelry', 'pet']:
            if not self.chara.slots.filter(type__en_name=kind, item__isnull=False).exists():
                raise serializers.ValidationError("該欄位無裝備")
        else:
            raise serializers.ValidationError("類型不存在")
        return kind
