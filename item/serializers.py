from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from item.models import Item
from chara.models import Chara

from item.use_effects import USE_EFFECT_CLASSES


class ItemWithNumberSerializer(BaseSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)

    def validate(self, data):
        item = data['id']
        if data['number'] > item.number:
            raise serializers.ValidationError("物品數量不足")
        item.number = data['number']
        return item


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
        item = self.instance.bag_items.filter(id=item_id).first()
        if item is None:
            raise serializers.ValidationError("背包中無此物品")
        if item.type.use_effect.id is None:
            raise serializers.ValidationError("此物品無法使用")

        return item


class SendItemSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)
    receiver = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    def save(self):
        sender = self.instance
        receiver = self.validated_data['receiver']
        items = self.validated_data['items']

        list(Chara.objects.filter(id__in=[sender.id, receiver.id]).select_for_update())

        items = sender.lose_items("bag", items, mode='return')
        receiver.get_items("bag", items)


class StorageTakeSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)

    def save(self):
        chara = self.instance
        items = self.validated_data['items']

        items = chara.lose_items("storage", items, mode='return')
        chara.get_items("bag", items)


class StoragePutSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)

    def save(self):
        chara = self.instance
        items = self.validated_data['items']

        items = chara.lose_items("bag", items, mode='return')
        chara.get_items("storage", items)
