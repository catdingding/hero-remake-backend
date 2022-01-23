from rest_framework import serializers
import serpy
from base.serializers import BaseSerializer, BaseModelSerializer, SerpyModelSerializer

from npc.models import NPC, NPCAttribute, NPCSkillSetting, NPCFavorite, NPCExchangeOption, NPCInfo, NPCCharaRelation
from item.models import Item
from world.serializers import AttributeTypeSerializer, ElementTypeSerializer
from ability.serializers import AbilitySerializer
from job.serializers import SkillSerializer
from item.serializers import ItemTypeSerializer


class NPCAttributeSerializer(SerpyModelSerializer):
    type = AttributeTypeSerializer()

    class Meta:
        model = NPCAttribute
        fields = ['type', 'value']


class NPCSkillSettingSerializer(SerpyModelSerializer):
    skill = SkillSerializer(fields=['name'])

    class Meta:
        model = NPCSkillSetting
        fields = ['skill', 'hp_percentage', 'mp_percentage',
                  'defender_hp_percentage', 'defender_mp_percentage', 'order']


class NPCCharaRelationSerializer(SerpyModelSerializer):
    class Meta:
        model = NPCCharaRelation
        fields = ['friendliness']


class NPCFavoriteSerializer(SerpyModelSerializer):
    item_type = ItemTypeSerializer(fields=['id', 'name'])

    class Meta:
        model = NPCFavorite
        fields = ['id', 'item_type', 'friendliness_reward']


class NPCExchangeOptionSerializer(SerpyModelSerializer):
    item_type = ItemTypeSerializer(fields=['id', 'name'])

    class Meta:
        model = NPCExchangeOption
        fields = ['id', 'item_type', 'friendliness_cost']


class NPCInfoSerializer(SerpyModelSerializer):
    class Meta:
        model = NPCInfo
        fields = ['description']


class NPCSerializer(SerpyModelSerializer):
    class Meta:
        model = NPC
        fields = ['id', 'name', 'has_image']


class NPCProfileSerializer(SerpyModelSerializer):
    element_type = ElementTypeSerializer(fields=['name'])
    abilities = AbilitySerializer(fields=['name'], many=True)

    attributes = NPCAttributeSerializer(many=True)
    skill_settings = NPCSkillSettingSerializer(many=True)
    favorites = NPCFavoriteSerializer(many=True)
    exchange_options = NPCExchangeOptionSerializer(many=True)
    chara_relation = serpy.MethodField()

    info = NPCInfoSerializer()

    class Meta:
        model = NPC
        fields = [
            'id', 'name', 'element_type', 'hp', 'mp', 'abilities', 'has_image',
            'attributes', 'skill_settings', 'favorites', 'exchange_options', 'chara_relation', 'info'
        ]

    def get_chara_relation(self, npc):
        return NPCCharaRelationSerializer(npc.chara_relations.filter(chara=self.chara).first()).data


class NPCFavoriteSubmitSerializer(BaseSerializer):
    favorite = serializers.PrimaryKeyRelatedField(queryset=NPCFavorite.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        favorite = self.validated_data['favorite']
        number = self.validated_data['number']
        relation, _ = NPCCharaRelation.objects.get_or_create(chara=self.chara, npc_id=favorite.npc_id)

        self.chara.lose_items('bag', [Item(type_id=favorite.item_type_id, number=number)])

        relation.friendliness += favorite.friendliness_reward * number
        relation.save()


class NPCExchangeOptionExchangeSerializer(BaseSerializer):
    exchange_option = serializers.PrimaryKeyRelatedField(queryset=NPCExchangeOption.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        option = self.validated_data['exchange_option']
        number = self.validated_data['number']
        relation, _ = NPCCharaRelation.objects.get_or_create(chara=self.chara, npc_id=option.npc_id)

        relation.friendliness -= option.friendliness_cost * number
        if relation.friendliness < 0:
            raise serializers.ValidationError("友好度不足")
        relation.save()

        self.chara.get_items('bag', [Item(type_id=option.item_type_id, number=number)])
