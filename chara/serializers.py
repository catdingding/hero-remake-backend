from django.db.models import F
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from world.models import SlotType
from chara.models import Chara, CharaIntroduction, CharaAttribute
from item.models import Item
from item.serializers import SimpleItemSerializer
from ability.serializers import AbilitySerializer
from country.serializers import CountrySerializer
from job.serializers import JobSerializer
from world.serializers import LocationSerializer, ElementTypeSerializer, AttributeTypeSerializer


class CharaAttributeSerialiser(BaseModelSerializer):
    type = AttributeTypeSerializer()

    class Meta:
        model = CharaAttribute
        fields = ['type', 'value', 'limit', 'proficiency']


class CharaProfileSerializer(BaseModelSerializer):
    location = LocationSerializer()
    country = CountrySerializer()
    element_type = ElementTypeSerializer()
    job = JobSerializer(fields=['name'])
    level = serializers.IntegerField()

    main_ability = AbilitySerializer(fields=['name'])
    job_ability = AbilitySerializer(fields=['name'])
    live_ability = AbilitySerializer(fields=['name'])
    abilities = AbilitySerializer(fields=['name'], many=True)

    bag_items = serializers.SerializerMethodField()
    storage_items = serializers.SerializerMethodField()

    attributes = CharaAttributeSerialiser(many=True)

    class Meta:
        model = Chara
        fields = '__all__'

    def get_bag_items(self, chara):
        return SimpleItemSerializer(
            [item for item in chara.bag_items.all().select_related('type', 'equipment')], many=True
        ).data

    def get_storage_items(self, chara):
        return SimpleItemSerializer(
            [item for item in chara.storage_items.all().select_related('type', 'equipment')], many=True
        ).data


class CharaIntroductionSerializer(BaseModelSerializer):
    class Meta:
        model = CharaIntroduction
        fields = ['content']


class SendMoneySerializer(BaseSerializer):
    gold = serializers.IntegerField(min_value=1)
    receiver_name = serializers.CharField()

    def save(self):
        receiver = self.validated_data['receiver']
        gold = self.validated_data['gold']

        self.chara.gold -= gold
        self.chara.save()
        Chara.objects.filter(id=receiver.id).update(gold=F('gold') + gold)

    def validate_gold(self, value):
        if value > self.chara.gold:
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
