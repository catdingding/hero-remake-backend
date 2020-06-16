from django.db.models import F
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from world.models import SlotType
from chara.models import Chara, CharaIntroduction
from item.models import Item


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


class SlotEquipSerializer(BaseSerializer):
    item = serializers.IntegerField()

    def save(self):
        chara = self.instance
        item = self.validated_data['item']
        slot = chara.slots.get(type=item.type.slot_type)

        chara.lose_items('bag', [item], mode='return')

        current_slot_item = slot.item
        slot.item = item
        slot.save()

        if current_slot_item is not None:
            chara.get_items('bag', [current_slot_item])

    def validate_item(self, item_id):
        item = self.instance.bag_items.filter(id=item_id).first()
        if item is None:
            raise serializers.ValidationError("背包中無此物品")
        if item.type.slot_type is None:
            raise serializers.ValidationError("此物品無法裝備")

        return item


class SlotDivestSerializer(BaseSerializer):
    slot_type = serializers.PrimaryKeyRelatedField(queryset=SlotType.objects.all())

    def save(self):
        chara = self.instance
        slot_type = self.validated_data['slot_type']
        slot = chara.slots.get(type=slot_type)

        current_slot_item = slot.item
        slot.item = None
        slot.save()

        if current_slot_item is not None:
            chara.get_items('bag', [current_slot_item])
