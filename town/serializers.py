from django.db.models import Sum
from rest_framework import serializers
from django.utils.timezone import localtime
from datetime import timedelta

from base.serializers import BaseSerializer, BaseModelSerializer, SerpyModelSerializer
from town.models import Town
from item.models import Item
from chara.models import Chara, CharaPartner

from chara.achievement import update_achievement_counter
from system.utils import push_log


class TownSerializer(SerpyModelSerializer):
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
    name = serializers.CharField(max_length=10)

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
        if kind in ['weapon', 'armor', 'jewelry', 'pet']:
            # 裝備改名次數
            update_achievement_counter(self.chara.id, 14, 1, 'increase')
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

    def validate(self, data):
        if data['kind'] in ['weapon', 'armor', 'jewelry', 'pet']:
            if '稀有' in data['name'] or '優良' in data['name']:
                raise serializers.ValidationError("名稱中不可帶有「稀有」或是「優良」")
        return data


class AltarSubmitSerializer(BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)
    chara = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    reward_settings = {
        1556: 100,
        1557: 25,
        1558: 1,
        1559: 50
    }

    def save(self):
        item = self.validated_data['item']
        number = self.validated_data['number']
        chara = self.validated_data['chara']

        self.chara.lose_items('bag', [Item(id=item.id, number=number)])

        if chara == self.chara:
            return {'display_message': f'檢測召喚對象……{chara.name}已出現，判定為已召喚成功'}

        minutes = self.reward_settings[item.type_id] * 5
        partner = CharaPartner.objects.filter(chara=self.chara, target_chara=chara).first()
        if partner is None:
            partner = CharaPartner(
                chara=self.chara, target_chara=chara,
                due_time=localtime() + timedelta(minutes=minutes)
            )
        else:
            partner.due_time = max(partner.due_time, localtime()) + timedelta(minutes=minutes)

        partner.save()

        return {'display_message': f"透過莫名其妙的獻祭，你成功召喚了{chara.name}的分身({minutes}分鐘)"}

    def validate_item(self, item):
        if item.type_id not in self.reward_settings:
            raise serializers.ValidationError("……祭壇毫無反應")
        return item
