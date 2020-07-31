from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from base.utils import randint
from world.models import SlotType
from item.models import Item, ItemType
from chara.models import Chara

from item.use_effects import USE_EFFECT_CLASSES


class SimpleItemSerializer(BaseSerializer):
    name = serializers.CharField(source="type.name")
    number = serializers.IntegerField()


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
        item = self.validated_data['item']
        number = self.validated_data['number']

        effect = USE_EFFECT_CLASSES[item.type.use_effect.id](item, number, self.chara)
        result = effect.execute()

        if item.type.is_consumable:
            item.number -= number
            if item.number == 0:
                item.delete()
            else:
                item.save()

        return {"detail": result}

    def validate(self, data):
        if data['number'] > data['item'].number:
            raise serializers.ValidationError("物品數量不足")
        return data

    def validate_item(self, item_id):
        item = self.chara.bag_items.filter(id=item_id).first()
        if item is None:
            raise serializers.ValidationError("背包中無此物品")
        if item.type.use_effect.id is None:
            raise serializers.ValidationError("此物品無法使用")

        return item


class SendItemSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)
    receiver = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    def save(self):
        sender = self.chara
        receiver = self.validated_data['receiver']
        items = self.validated_data['items']

        list(Chara.objects.filter(id__in=[sender.id, receiver.id]).select_for_update())

        items = sender.lose_items("bag", items, mode='return')
        receiver.get_items("bag", items)


class StorageTakeSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)

    def save(self):
        items = self.validated_data['items']

        items = self.chara.lose_items("storage", items, mode='return')
        self.chara.get_items("bag", items)


class StoragePutSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)

    def save(self):
        items = self.validated_data['items']

        items = self.chara.lose_items("bag", items, mode='return')
        self.chara.get_items("storage", items)


class SmithUpgradeSerializer(BaseSerializer):
    quality_limit = {
        '普通': 50,
        '優良': 60,
        '稀有': 70
    }
    slot_type_add_on = {
        'weapon': {'attack_add_on': 5, 'weight_add_on': -1},
        'armor': {'defense_add_on': 5, 'weight_add_on': -1},
        'jewelry': {'attack_add_on': 1, 'weight_add_on': -1}
    }

    slot_type = serializers.PrimaryKeyRelatedField(queryset=SlotType.objects.all())
    times = serializers.IntegerField(min_value=1)

    def save(self):
        equipment = self.validated_data['equipment']
        times = self.validated_data['times']

        self.chara.lose_items(
            'bag', ItemType.objects.get(element_type=equipment.element_type, category=4).make(3 * times)
        )
        self.chara.lose_proficiency(1500 * times)
        self.chara.save()

        equipment.upgrade_times += times
        for field, value in self.slot_type_add_on[equipment.type.slot_type_id].items():
            setattr(equipment, field, getattr(equipment, field) + value * times)

        equipment.save()

    def validate_slot_type(self, value):
        if value.id == 'pet':
            raise serializers.ValidationError("寵物無法於工房強化")
        return value

    def validate(self, data):
        item = self.chara.slots.get(type=data['slot_type']).item
        if item is None:
            raise serializers.ValidationError("該裝備欄未裝備")

        equipment = item.equipment
        upgrade_limit = self.quality_limit[equipment.quality]
        if equipment.upgrade_times + data['times'] > upgrade_limit:
            raise serializers.ValidationError("剩餘強化次數不足")

        data['equipment'] = equipment
        return data


class SmithReplaceAbilitySerializer(BaseSerializer):
    slot_type = serializers.PrimaryKeyRelatedField(queryset=SlotType.objects.all())
    source_item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())

    def save(self):
        equipment = self.validated_data['equipment']
        source_item = self.validated_data['source_item']

        # 以裝備注入
        if source_item.type.category_id == 1:
            source_equipment = source_item.equipment
            cost = 50 - source_equipment.attack - source_equipment.defense + source_equipment.weight * 3
            if source_equipment.element_type == equipment.element_type:
                cost -= 10
                if self.chara.element_type == equipment.element_type:
                    cost -= 10
            equipment.ability_1 = source_equipment.ability_1
        # 以奧義石注入
        elif source_item.type.category_id == 3:
            cost = 50
            equipment.ability_2 = source_item.type.ability_1

        cost = max(0, cost)
        self.chara.lose_proficiency(cost * 500)
        self.chara.save()

        self.chara.lose_items('bag', [Item(id=source_item.id, number=1)])

        if 50 >= randint(1, 100):
            equipment.save()
            return {"detail": "注入成功"}
        else:
            return {"detail": "注入失敗"}

    def validate(self, data):
        item = self.chara.slots.get(type=data['slot_type']).item
        if item is None:
            raise serializers.ValidationError("該裝備欄未裝備")
        data['equipment'] = item.equipment

        if data['source_item'].type.slot_type != data['equipment'].type.slot_type:
            raise serializers.ValidationError("裝備欄位不符")

        return data
