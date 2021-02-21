from django.db.models import F
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from world.models import SlotType
from chara.models import Chara, CharaIntroduction, CharaAttribute, BattleMapTicket, CharaSlot, CharaSkillSetting
from item.models import Item
from battle.serializers import BattleMapSerializer
from item.serializers import SimpleItemSerializer, ItemSerializer
from ability.serializers import AbilitySerializer
from country.serializers import CountrySerializer, CountryOfficialSerializer

from world.serializers import SlotTypeSerializer, LocationSerializer, ElementTypeSerializer, AttributeTypeSerializer


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


class CharaProfileSerializer(BaseModelSerializer):
    from job.serializers import JobSerializer

    location = LocationSerializer()
    country = CountrySerializer()
    official = CountryOfficialSerializer()
    is_king = serializers.SerializerMethodField()
    element_type = ElementTypeSerializer()
    job = JobSerializer(fields=['name', 'attribute_type'])
    level = serializers.IntegerField()

    main_ability = AbilitySerializer(fields=['id', 'name'])
    job_ability = AbilitySerializer(fields=['id', 'name'])
    live_ability = AbilitySerializer(fields=['id', 'name'])

    slots = CharaSlotSerializer(many=True)
    bag_items = serializers.SerializerMethodField()
    skill_settings = CharaSkillSettingSerializer(many=True)

    attributes = CharaAttributeSerialiser(many=True)
    battle_map_tickets = BattleMapTicketSerialiser(many=True)

    introduction = CharaIntroductionSerializer()

    class Meta:
        model = Chara
        exclude = ['user', 'created_at', 'updated_at', 'abilities', 'storage_items']

    def get_bag_items(self, chara):
        return ItemSerializer(
            chara.bag_items.all().select_related('type__slot_type', 'equipment__ability_1', 'equipment__ability_2'), many=True
        ).data

    def get_slots(self, chara):
        return CharaSlotSerializer(
            chara.slots.all().select_related('type', 'item__equipment__ability_1', 'item__equipment__ability_2', 'item__type'), many=True
        ).data

    def get_is_king(self, chara):
        return hasattr(chara, 'king_of')


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
