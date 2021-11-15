from random import choices, random, choice, gauss

import serpy
from django.db.models import F
from rest_framework import serializers
import serpy
from base.serializers import (
    BaseSerializer, BaseModelSerializer, TransferPermissionCheckerMixin,
    SerpyModelSerializer, LockedEquipmentCheckMixin
)

from base.utils import randint
from ability.serializers import AbilitySerializer
from battle.models import BattleMap
from world.serializers import SlotTypeSerializer, ElementTypeSerializer
from world.models import SlotType, ElementType
from item.models import Item, ItemType, Equipment, PetType
from chara.models import Chara, BattleMapTicket

from item.use_effects import USE_EFFECT_CLASSES
from system.utils import push_log, send_private_message_by_system


class SimpleItemSerializer(SerpyModelSerializer):
    name = serpy.MethodField()
    number = serpy.Field()

    def get_name(self, obj):
        return obj.type.name


class ItemTypeSerializer(SerpyModelSerializer):
    element_type = ElementTypeSerializer()
    slot_type = SlotTypeSerializer()
    ability_1 = AbilitySerializer(fields=['name'])
    ability_2 = AbilitySerializer(fields=['name'])

    class Meta:
        model = ItemType
        exclude = ['created_at', 'updated_at']


class EquipmentSerializer(SerpyModelSerializer):
    attack = serpy.IntField()
    defense = serpy.IntField()
    weight = serpy.IntField()
    upgrade_times_limit = serpy.IntField()
    display_name = serpy.StrField()
    element_type = ElementTypeSerializer()

    ability_1 = AbilitySerializer(fields=['name'])
    ability_2 = AbilitySerializer(fields=['name'])

    class Meta:
        model = Equipment
        exclude = ['created_at', 'updated_at']


class ItemSerializer(SerpyModelSerializer):
    type = ItemTypeSerializer(omit=['ability_1', 'ability_2'])
    equipment = EquipmentSerializer(required=False)
    name = serpy.MethodField()

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


class SendItemSerializer(LockedEquipmentCheckMixin, TransferPermissionCheckerMixin, BaseSerializer):
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

        push_log("傳送", f"{sender.name}向{receiver.name}傳送了{item.name}*{item.number}")
        send_private_message_by_system(
            sender.id, receiver.id, f"{sender.name}向{receiver.name}傳送了{item.name}*{item.number}")

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

    def save(self, no_cost=False):
        times = self.validated_data['times']
        item = self.validated_data['item']
        equipment = item.equipment
        pet_type = item.type.pet_type

        if not no_cost:
            self.chara.lose_proficiency(pet_type.upgrade_proficiency_cost * times)
            self.chara.save()

        if equipment.upgrade_times < equipment.upgrade_times_limit:
            equipment.upgrade_times += times
            equipment.attack_add_on += pet_type.attack_growth * times
            equipment.defense_add_on += pet_type.defense_growth * times
            equipment.weight_add_on += pet_type.weight_growth * times
        else:
            orig_name = equipment.display_name

            targets = pet_type.evolution_targets.all()
            target_item_type = choices(targets, weights=[x.weight for x in targets])[0].target_pet_type.item_type
            equipment.type = target_item_type
            equipment.upgrade_times = 0
            equipment.attack_add_on = 0
            equipment.defense_add_on = 0
            equipment.weight_add_on = 0

            if equipment.custom_name == pet_type.item_type.name:
                equipment.custom_name = target_item_type.name

            push_log("進化", f"{self.chara.name}的{orig_name}進化為{target_item_type.name}")

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
            if equipment.upgrade_times == 10 and data['times'] > 1:
                raise serializers.ValidationError(f"轉生時請勿投入多次升級資源")

        data['item'] = item
        return data


class SmithReplaceAbilitySerializer(LockedEquipmentCheckMixin, BaseSerializer):
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

            # 寵物可用飾品奧義石注入ability_1
            if equipment.type.slot_type_id == 4 and source_item.type.slot_type_id == 3:
                equipment.ability_1 = ability
            else:
                equipment.ability_2 = ability

        cost = max(0, cost)
        self.chara.lose_proficiency(cost * 500)
        self.chara.save()

        self.chara.lose_items('bag', [Item(id=source_item.id, number=1)])

        if 30 + (40 * self.chara.luck_sigmoid) >= randint(1, 100):
            equipment.save()
            push_log("製作", f"{self.chara.name}成功的將「{ability.name}」注入了{equipment.display_name}")
            return {"display_message": "注入成功"}
        else:
            push_log("製作", f"{self.chara.name}嘗試用{source_item.name}將「{ability.name}」注入了{equipment.display_name}，但失敗了")
            return {"display_message": "注入失敗"}

    def validate_source_item(self, source_item):
        return self.validate_item(source_item)

    def validate(self, data):
        item = self.chara.slots.get(type=data['slot_type']).item
        if item is None:
            raise serializers.ValidationError("該裝備欄未裝備")
        data['equipment'] = item.equipment

        if data['source_item'].type.slot_type != data['equipment'].type.slot_type:
            # 寵物可用飾品奧義石注入ability_1
            if not (data['equipment'].type.slot_type_id == 4 and data['source_item'].type.slot_type_id == 3 and data['source_item'].type.category_id == 3):
                raise serializers.ValidationError("裝備欄位不符")

        return data


class SmithReplaceElementTypeSerializer(BaseSerializer):
    slot_type = serializers.PrimaryKeyRelatedField(queryset=SlotType.objects.all())
    new_element_type = serializers.PrimaryKeyRelatedField(queryset=ElementType.objects.all())

    def save(self):
        equipment = self.validated_data['equipment']

        equipment.upgrade_times = 0
        equipment.attack_add_on = 0
        equipment.defense_add_on = 0
        equipment.weight_add_on = 0
        equipment.element_type = self.validated_data['new_element_type']

        equipment.save()

    def validate_slot_type(self, value):
        if value.id == 4:
            raise serializers.ValidationError("寵物無法更改屬性")
        return value

    def validate(self, data):
        item = self.chara.slots.get(type=data['slot_type']).item
        if item is None:
            raise serializers.ValidationError("該裝備欄未裝備")

        equipment = item.equipment
        if equipment.upgrade_times < equipment.upgrade_times_limit:
            raise serializers.ValidationError("尚未強化滿級")

        data['equipment'] = equipment
        return data


class SmithEquipmentTransformSerializer(LockedEquipmentCheckMixin, BaseSerializer):
    item_1 = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    item_2 = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    item_3 = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())

    def save(self):
        items = self.validated_data['items']

        # 自定義裝備
        item, = ItemType.objects.get(id__in=[1578, 1579, 1580], slot_type=items[0].type.slot_type_id).make(1)
        equipment = item.equipment

        rare_rate = 20 + sum(1 for x in items if x.equipment.quality == '稀有') * 30
        equipment.quality = '稀有' if rare_rate >= randint(1, 100) else '普通'

        equipment.element_type_id = choice([x.equipment.element_type_id for x in items])

        equipment.ability_1_id = choice([x.equipment.ability_1_id for x in items])
        equipment.ability_2_id = choice([x.equipment.ability_2_id for x in items])

        equipment.attack_base = self.compute_equipment_param(items, 'attack')
        equipment.defense_base = self.compute_equipment_param(items, 'defense')
        equipment.weight_base = self.compute_equipment_param(items, 'weight')

        equipment.save()
        self.chara.lose_items('bag', items)
        self.chara.get_items('bag', [item])

        return {'display_message': f"獲得了{item.name}({equipment.attack_base}/{equipment.defense_base}/{equipment.weight_base})"}

    def compute_equipment_param(self, items, field):
        average = sum(getattr(x.type, field) for x in items) / len(items)
        return int(gauss(average, average * 0.25))

    def validate(self, data):
        items = list(data.values())

        if len({x.type.slot_type_id for x in items}) != 1:
            raise serializers.ValidationError("裝備部位必須相同")

        if items[0].type.slot_type_id == 4:
            raise serializers.ValidationError("寵物不可轉換")

        if len({x.type.id for x in items}) != 3:
            raise serializers.ValidationError("裝備類型不可重複")

        for item in items:
            if item.type_id in [1578, 1579, 1580]:
                raise serializers.ValidationError("轉換所生成的裝備，無法再次投入轉換")

        return {'items': items}


class BattleMapTicketToItemSerializer(BaseSerializer):
    battle_map = serializers.PrimaryKeyRelatedField(queryset=BattleMap.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        battle_map, number = [self.validated_data[x] for x in ['battle_map', 'number']]
        BattleMapTicket.objects.filter(chara=self.chara, battle_map=battle_map).update(value=F('value') - number)
        item_type = ItemType.objects.get(use_effect=6, use_effect_param=battle_map.id)

        if random() <= 0.8:
            items = item_type.make(number)
            self.chara.get_items('bag', items)

            return {'display_message': f"成功的製作了{number}個{item_type.name}"}
        else:
            push_log("製作", f"{self.chara.name}製作地圖時不小心打翻了墨水，損毀了{number}個{item_type.name}")
            return {'display_message': "不小心打翻了墨水，所有的地圖都被損毀了"}

    def validate(self, data):
        if not BattleMapTicket.objects.filter(chara=self.chara, battle_map=data['battle_map'], value__gte=data['number']).exists():
            raise serializers.ValidationError("地圖剩餘次數不足")

        return data


class ToggleEquipmentLockSerializer(BaseSerializer):
    slot_type = serializers.PrimaryKeyRelatedField(queryset=SlotType.objects.all())

    def save(self):
        slot_type = self.validated_data['slot_type']

        equipment = self.chara.slots.get(type=slot_type).item.equipment
        equipment.is_locked = not equipment.is_locked
        equipment.save()

    def validate_slot_type(self, slot_type):
        if not self.chara.slots.filter(type=slot_type, item__isnull=False).exists():
            raise serializers.ValidationError("該欄位無裝備")
        return slot_type


class PetTypeSerializer(SerpyModelSerializer):
    item_type = ItemTypeSerializer(fields=['name', 'attack', 'defense', 'weight', 'element_type'])

    class Meta:
        model = PetType
        fields = ['item_type', 'upgrade_proficiency_cost', 'attack_growth', 'defense_growth', 'weight_growth']
