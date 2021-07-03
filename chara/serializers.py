from django.db.models import F, Prefetch
from rest_framework import serializers
from rest_flex_fields import is_included
from base.utils import randint, format_currency
from base.serializers import BaseSerializer, BaseModelSerializer

from world.models import SlotType
from chara.models import Chara, CharaIntroduction, CharaAttribute, BattleMapTicket, CharaRecord, CharaSlot, CharaSkillSetting
from item.models import Item, ItemTypePoolGroup
from battle.serializers import BattleMapSerializer
from item.serializers import SimpleItemSerializer, ItemSerializer
from ability.serializers import AbilitySerializer
from country.serializers import CountrySerializer, CountryOfficialSerializer

from world.serializers import SlotTypeSerializer, LocationSerializer, ElementTypeSerializer, AttributeTypeSerializer
from system.utils import push_log, send_private_message_by_system


class BattleMapTicketSerialiser(BaseModelSerializer):
    battle_map = BattleMapSerializer()

    class Meta:
        model = BattleMapTicket
        fields = ['battle_map', 'value']


class CharaAttributeSerialiser(BaseModelSerializer):
    type = AttributeTypeSerializer()

    class Meta:
        model = CharaAttribute
        fields = ['type', 'value', 'limit', 'proficiency']


class CharaSlotSerializer(BaseModelSerializer):
    type = SlotTypeSerializer()
    item = ItemSerializer()

    class Meta:
        model = CharaSlot
        fields = ['type', 'item']


class CharaSkillSettingSerializer(BaseModelSerializer):
    class Meta:
        model = CharaSkillSetting
        fields = ['skill', 'hp_percentage', 'mp_percentage', 'order']


class CharaIntroductionSerializer(BaseModelSerializer):
    class Meta:
        model = CharaIntroduction
        fields = ['content']


class CharaRecordSerializer(BaseModelSerializer):
    class Meta:
        model = CharaRecord
        exclude = ['id', 'created_at', 'updated_at']


class CharaPublicProfileSerializer(BaseModelSerializer):
    from job.serializers import JobSerializer

    country = CountrySerializer()
    official = CountryOfficialSerializer()

    job = JobSerializer(fields=['name', 'attribute_type'])
    level = serializers.IntegerField()
    element_type = ElementTypeSerializer()

    main_ability = AbilitySerializer(fields=['id', 'name'])
    job_ability = AbilitySerializer(fields=['id', 'name'])
    live_ability = AbilitySerializer(fields=['id', 'name'])

    slots = CharaSlotSerializer(many=True)
    attributes = CharaAttributeSerialiser(many=True)

    introduction = CharaIntroductionSerializer()
    record = CharaRecordSerializer()

    class Meta:
        model = Chara
        exclude = [
            'user', 'created_at', 'updated_at', 'abilities', 'storage_items',
            'location', 'bag_items', 'gold', 'proficiency', 'next_action_time', 'health',
            'member_point', 'has_cold_down_bonus', 'has_quest_bonus', 'has_auto_heal'
        ]

    @classmethod
    def process_queryset(cls, request, queryset):
        for field in ['country', 'official', 'element_type', 'job', 'main_ability', 'job_ability', 'live_ability', 'record', 'introduction']:
            if is_included(request, field):
                queryset = queryset.select_related(field)

        if is_included(request, 'job'):
            queryset = queryset.select_related('job__attribute_type')

        if is_included(request, 'slots'):
            queryset = queryset.prefetch_related(Prefetch('slots', CharaSlot.objects.select_related(
                'type', 'item__type__slot_type', 'item__equipment__ability_1', 'item__equipment__ability_2', 'item__equipment__element_type'
            )))

        if is_included(request, 'attributes'):
            queryset = queryset.prefetch_related(Prefetch('attributes', CharaAttribute.objects.select_related(
                'type'
            )))

        return queryset


class CharaProfileSerializer(CharaPublicProfileSerializer):
    location = LocationSerializer()
    is_king = serializers.SerializerMethodField()

    hp_limit = serializers.IntegerField()
    mp_limit = serializers.IntegerField()

    bag_items = ItemSerializer(many=True)
    skill_settings = CharaSkillSettingSerializer(many=True)

    battle_map_tickets = BattleMapTicketSerialiser(many=True)

    class Meta:
        model = Chara
        exclude = [
            'user', 'created_at', 'updated_at', 'abilities', 'storage_items'
        ]

    def get_is_king(self, chara):
        return hasattr(chara, 'king_of')

    @classmethod
    def process_queryset(cls, request, queryset):
        queryset = super().process_queryset(request, queryset)

        if is_included(request, 'location'):
            queryset = queryset.select_related('location__country', 'location__town',
                                               'location__element_type', 'location__battle_map')
        if is_included(request, 'is_king'):
            queryset = queryset.select_related('king_of')

        if is_included(request, 'bag_items'):
            queryset = queryset.prefetch_related(Prefetch('bag_items', Item.objects.select_related(
                'type__slot_type', 'equipment__ability_1', 'equipment__ability_2', 'equipment__element_type'
            )))

        if is_included(request, 'battle_map_tickets'):
            queryset = queryset.prefetch_related(Prefetch('battle_map_tickets', BattleMapTicket.objects.select_related(
                'battle_map'
            )))
        if is_included(request, 'skill_settings'):
            queryset = queryset.prefetch_related('skill_settings')

        return queryset


class SendGoldSerializer(BaseSerializer):
    gold = serializers.IntegerField(min_value=1)
    receiver = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    def save(self):
        receiver = self.validated_data['receiver']
        gold = self.validated_data['gold']

        list(Chara.objects.filter(id__in=[self.chara.id, receiver.id]).select_for_update())

        self.chara.lose_gold(gold)
        self.chara.save()

        receiver.gold += gold
        receiver.save()

        push_log("傳送", f"{self.chara.name}向{receiver.name}傳送了{format_currency(gold)}金錢")
        send_private_message_by_system(
            self.chara, receiver, f"{self.chara.name}向{receiver.name}傳送了{format_currency(gold)}金錢")

    def validate_receiver(self, value):
        if value == self.chara:
            raise serializers.ValidationError("不可傳送給自己")
        return value


class SlotEquipSerializer(BaseSerializer):
    item = serializers.IntegerField()

    def save(self):
        item = self.validated_data['item']
        slot = self.chara.slots.get(type=item.type.slot_type)

        self.chara.lose_items('bag', [item], mode='return')

        current_slot_item = slot.item
        slot.item = item
        slot.save()

        if current_slot_item is not None:
            self.chara.get_items('bag', [current_slot_item])

    def validate_item(self, item_id):
        item = self.chara.bag_items.filter(id=item_id).first()
        if item is None:
            raise serializers.ValidationError("背包中無此物品")
        if item.type.category_id != 1:
            raise serializers.ValidationError("此物品無法裝備")

        return item


class SlotDivestSerializer(BaseSerializer):
    slot_type = serializers.PrimaryKeyRelatedField(queryset=SlotType.objects.all())

    def save(self):
        slot_type = self.validated_data['slot_type']
        slot = self.chara.slots.get(type=slot_type)

        current_slot_item = slot.item
        slot.item = None
        slot.save()

        if current_slot_item is not None:
            self.chara.get_items('bag', [current_slot_item])


class RestSerializer(BaseSerializer):
    def save(self):
        chara = self.chara
        chara.hp = max(chara.hp, int(chara.hp_max * chara.health / 100))
        chara.mp = max(chara.mp, int(chara.mp_max * chara.health / 100))
        chara.save()


class IncreaseHPMPMaxSerializer(BaseSerializer):
    def save(self):
        self.chara.lose_gold(self.validated_data['gold_cost'])

        hp_max_orig = self.chara.hp_max
        mp_max_orig = self.chara.mp_max
        self.chara.hp_max = min(self.chara.hp_limit, self.chara.hp_max + 250 + randint(0, 250))
        self.chara.mp_max = min(self.chara.mp_limit, self.chara.mp_max + 120 + randint(0, 120))

        self.chara.save()
        return {"display_message": f"增加了{self.chara.hp_max-hp_max_orig}HP上限、{self.chara.mp_max-mp_max_orig}MP上限"}

    def validate(self, data):
        cost = self.chara.hp_max + self.chara.mp_max
        cost += sum(attr.value for attr in self.chara.attrs.values())
        cost *= 5000
        cost = max(1000000, cost)
        data['gold_cost'] = cost
        return data


class HandInQuestSerializer(BaseSerializer):
    quest = serializers.CharField()

    quest_requirements = {
        'world_monster_quest': 100,
        'country_monster_quest': 400
    }

    def save(self):
        if self.chara.has_quest_bonus:
            orig = getattr(self.chara.record, self.validated_data['counter'])
            cost = self.quest_requirements[self.validated_data['quest']]
            setattr(self.chara.record, self.validated_data['counter'], orig - cost)
        else:
            setattr(self.chara.record, self.validated_data['counter'], 0)
        self.chara.record.save()

        # 任務池
        items = ItemTypePoolGroup.objects.get(id=9).pick()
        self.chara.get_items('bag', items)

        gold = 5000000
        proficiency = 500

        self.chara.gold += gold
        self.chara.proficiency += proficiency
        self.chara.save()

        return {"display_message": f"獲得了{gold}金錢、{proficiency}熟練、{'、'.join(f'{x.type.name}*{x.number}' for x in items)}"}

    def validate(self, data):
        data['counter'] = data['quest'] + '_counter'
        if not hasattr(self.chara.record, data['counter']):
            raise serializers.ValidationError("任務不存在")

        if getattr(self.chara.record, data['counter']) < self.quest_requirements[data['quest']]:
            raise serializers.ValidationError("數量不足")

        return data
