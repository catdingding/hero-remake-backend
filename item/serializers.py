from random import choices

from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from base.utils import randint
from ability.serializers import AbilitySerializer
from world.serializers import SlotTypeSerializer, ElementTypeSerializer
from world.models import SlotType
from item.models import Item, ItemType, Equipment
from chara.models import Chara

from item.use_effects import USE_EFFECT_CLASSES
from system.utils import push_log


class SimpleItemSerializer(BaseSerializer):
    name = serializers.CharField(source="type.name")
    number = serializers.IntegerField()


class ItemTypeSerializer(BaseModelSerializer):
    slot_type = SlotTypeSerializer()
    ability_1 = AbilitySerializer(fields=['name'])
    ability_2 = AbilitySerializer(fields=['name'])

    class Meta:
        model = ItemType
        exclude = ['created_at', 'updated_at']


class EquipmentSerializer(BaseModelSerializer):
    attack = serializers.IntegerField()
    defense = serializers.IntegerField()
    weight = serializers.IntegerField()
    upgrade_times_limit = serializers.IntegerField()
    display_name = serializers.CharField()
    element_type = ElementTypeSerializer()

    ability_1 = AbilitySerializer(fields=['name'])
    ability_2 = AbilitySerializer(fields=['name'])

    class Meta:
        model = Equipment
        exclude = ['created_at', 'updated_at']


class ItemSerializer(BaseModelSerializer):
    type = ItemTypeSerializer(omit=['ability_1', 'ability_2'])
    equipment = EquipmentSerializer()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Item
        exclude = ['created_at', 'updated_at']

    def get_name(self, obj):
        return obj.equipment.display_name if hasattr(obj, 'equipment') else obj.type.name


class UseItemSerializer(BaseSerializer):
    item = serializers.IntegerField()
    number = serializers.IntegerField(min_value=1)

    def save(self):
        item = self.validated_data['item']
        number = self.validated_data['number']

        effect = USE_EFFECT_CLASSES[item.type.use_effect.id](item, number, self.chara)
        message = effect.execute()

        if item.type.is_consumable:
            item.number -= number
            if item.number == 0:
                item.delete()
            else:
                item.save()

        return {"display_message": message}

    def validate(self, data):
        if data['number'] > data['item'].number:
            raise serializers.ValidationError("物品數量不足")
        return data

    def validate_item(self, item_id):
        item = self.chara.bag_items.filter(id=item_id).first()
        if item is None:
            raise serializers.ValidationError("背包中無此物品")
        if item.type.use_effect_id is None:
            raise serializers.ValidationError("此物品無法使用")

        return item


class SendItemSerializer(BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)
    receiver = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    def save(self):
        sender = self.chara
        receiver = self.validated_data['receiver']

        item = self.validated_data['item']
        item.number = self.validated_data['number']
        items = [item]

        list(Chara.objects.filter(id__in=[sender.id, receiver.id]).select_for_update())

        items = sender.lose_items("bag", items, mode='return')
        receiver.get_items("bag", items)

        push_log("傳送", f"{sender.name}向{receiver.name}傳送了{item.type.name}*{item.number}")

    def validate_receiver(self, value):
        if value == self.chara:
            raise serializers.ValidationError("不可傳送給自己")
        return value


class StorageTakeSerializer(BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        item = self.validated_data['item']
        item.number = self.validated_data['number']
        items = [item]

        items = self.chara.lose_items("storage", items, mode='return')
        self.chara.get_items("bag", items)


class StoragePutSerializer(BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        item = self.validated_data['item']
        item.number = self.validated_data['number']
        items = [item]

        items = self.chara.lose_items("bag", items, mode='return')
        self.chara.get_items("storage", items)


class SmithUpgradeSerializer(BaseSerializer):
    slot_type_add_on = {
        1: {'attack_add_on': 5, 'weight_add_on': -1},  # weapon
        2: {'defense_add_on': 5, 'weight_add_on': -1},  # armor
        3: {'attack_add_on': 1, 'weight_add_on': -1}  # jewelry
    }

    slot_type = serializers.PrimaryKeyRelatedField(queryset=SlotType.objects.all())
    times = serializers.IntegerField(min_value=1)

    def save(self):
        equipment = self.validated_data['equipment']
        times = self.validated_data['times']

        self.chara.lose_items(
            'bag', ItemType.objects.get(element_type=equipment.element_type, category=4).make(3 * times)
        )
        self.chara.lose_gold(15000000 * times)
        self.chara.save()

        equipment.upgrade_times += times
        for field, value in self.slot_type_add_on[equipment.type.slot_type_id].items():
            setattr(equipment, field, getattr(equipment, field) + value * times)

        equipment.save()

    def validate_slot_type(self, value):
        if value.id == 4:
            raise serializers.ValidationError("寵物無法於工房強化")
        return value

    def validate(self, data):
        item = self.chara.slots.get(type=data['slot_type']).item
        if item is None:
            raise serializers.ValidationError("該裝備欄未裝備")

        equipment = item.equipment
        if equipment.upgrade_times + data['times'] > equipment.upgrade_times_limit:
            raise serializers.ValidationError("剩餘強化次數不足")

        data['equipment'] = equipment
        return data


class PetUpgradeSerializer(BaseSerializer):
    times = serializers.IntegerField(min_value=1)

    def save(self):
        times = self.validated_data['times']
        item = self.validated_data['item']
        equipment = item.equipment
        pet_type = item.type.pet_type

        self.chara.lose_proficiency(pet_type.upgrade_proficiency_cost * times)
        self.chara.save()

        if equipment.upgrade_times < equipment.upgrade_times_limit:
            equipment.upgrade_times += times
            equipment.attack_add_on += pet_type.attack_growth
            equipment.defense_add_on += pet_type.defense_growth
            equipment.weight_add_on += pet_type.weight_growth
        else:
            targets = pet_type.evolution_targets.all()
            target_item_type = choices(targets, weights=[x.weight for x in targets])[0].target_pet_type.item_type
            equipment.type = target_item_type
            equipment.upgrade_times = 0
            equipment.attack_add_on = 0
            equipment.defense_add_on = 0
            equipment.weight_add_on = 0

            if equipment.custom_name == pet_type.item_type.name:
                equipment.custom_name = target_item_type.name

        equipment.save()

    def validate(self, data):
        item = self.chara.slots.get(type=4).item
        if item is None:
            raise serializers.ValidationError("未裝備寵物")

        equipment = item.equipment
        pet_type = item.type.pet_type
        if equipment.upgrade_times + data['times'] > equipment.upgrade_times_limit:
            if equipment.upgrade_times != 10 or not pet_type.evolution_targets.exists():
                raise serializers.ValidationError(f"當前寵物無法繼續升級或轉生")

        data['item'] = item
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
            cost = 50 - (source_equipment.attack + source_equipment.defense - source_equipment.weight * 3) // 10
            if source_equipment.element_type == equipment.element_type:
                cost -= 10
                if self.chara.element_type == equipment.element_type:
                    cost -= 10
            ability = source_equipment.ability_1
            equipment.ability_1 = ability
        # 以奧義石注入
        elif source_item.type.category_id == 3:
            cost = 50
            ability = source_item.type.ability_1
            equipment.ability_2 = ability

        cost = max(0, cost)
        self.chara.lose_proficiency(cost * 500)
        self.chara.save()

        self.chara.lose_items('bag', [Item(id=source_item.id, number=1)])

        if 50 >= randint(1, 100):
            equipment.save()
            push_log("製作", f"{self.chara.name}成功的將「{ability.name}」注入了{equipment.display_name}")
            return {"display_message": "注入成功"}
        else:
            push_log("製作", f"{self.chara.name}嘗試將「{ability.name}」注入了{equipment.display_name}，但失敗了")
            return {"display_message": "注入失敗"}

    def validate(self, data):
        item = self.chara.slots.get(type=data['slot_type']).item
        if item is None:
            raise serializers.ValidationError("該裝備欄未裝備")
        data['equipment'] = item.equipment

        if data['source_item'].type.slot_type != data['equipment'].type.slot_type:
            raise serializers.ValidationError("裝備欄位不符")

        return data
