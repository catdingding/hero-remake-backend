from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from item.models import Item

from item.use_effects import USE_EFFECT_CLASSES


class UseItemSerializer(BaseSerializer):
    item = serializers.IntegerField()
    number = serializers.IntegerField(min_value=1)

    def save(self):
        chara = self.instance
        item = self.validated_data['item']
        number = self.validated_data['number']

        effect = USE_EFFECT_CLASSES[item.type.use_effect.id](item, number, chara)
        result = effect.execute()

        if item.type.is_consumable:
            item.number -= number
            if item.number == 0:
                item.delete()
            else:
                item.save()

        return result

    def validate(self, data):
        if data['number'] > data['item'].number:
            raise serializers.ValidationError("物品數量不足")
        return data

    def validate_item(self, item_id):
        item = self.instance.bag_items.filter(id=item_id).select_for_update().first()
        if item is None:
            raise serializers.ValidationError("背包中無此物品")
        if item.type.use_effect.id is None:
            raise serializers.ValidationError("此物品無法使用")

        return item
