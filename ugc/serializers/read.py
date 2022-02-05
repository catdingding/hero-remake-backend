import serpy
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer, SerpyModelSerializer

from ugc.models import (
    UGCMonster, UGCMonsterAttribute, UGCMonsterSkillSetting,
    UGCDungeon, UGCDungeonFloor, UGCDungeonFloorMonster,
    CharaUGCDungeonRecord
)
from ability.serializers import AbilitySerializer
from chara.serializers import CharaProfileSerializer
from job.serializers import SkillSerializer
from world.serializers import AttributeTypeSerializer


class UGCMonsterAttributeSerializer(SerpyModelSerializer):
    type = AttributeTypeSerializer()

    class Meta:
        model = UGCMonsterAttribute
        fields = ['type', 'value']


class UGCMonsterSkillSettingSerializer(SerpyModelSerializer):
    skill = SkillSerializer(fields=['name'])

    class Meta:
        model = UGCMonsterSkillSetting
        fields = ['skill', 'hp_percentage', 'mp_percentage',
                  'defender_hp_percentage', 'defender_mp_percentage', 'order']


class UGCMonsterSerializer(SerpyModelSerializer):
    chara = CharaProfileSerializer(fields=['id', 'name'])
    abilities = AbilitySerializer(fields=['id', 'name'], many=True)
    attributes = UGCMonsterAttributeSerializer(many=True)
    skill_settings = UGCMonsterSkillSettingSerializer(many=True)

    class Meta:
        model = UGCMonster
        fields = ['id', 'chara', 'name', 'element_type', 'hp', 'mp', 'abilities', 'attributes', 'skill_settings']


class UGCDungeonFloorMonsterSerializer(SerpyModelSerializer):
    monster = UGCMonsterSerializer(fields=['id', 'name'])

    class Meta:
        model = UGCDungeonFloorMonster
        fields = ['monster']


class UGCDungeonFloorSerializer(SerpyModelSerializer):
    monsters = UGCDungeonFloorMonsterSerializer(many=True)

    class Meta:
        model = UGCDungeonFloor
        fields = ['monsters']


class CharaUGCDungeonRecordSerializer(SerpyModelSerializer):
    class Meta:
        model = CharaUGCDungeonRecord
        fields = ['status', 'start_floor', 'current_floor']


class UGCDungeonSerializer(SerpyModelSerializer):
    chara = CharaProfileSerializer(fields=['id', 'name'])
    floors = UGCDungeonFloorSerializer(many=True)
    record = serpy.MethodField()

    class Meta:
        model = UGCDungeon
        fields = ['id', 'chara', 'record', 'name', 'description', 'max_floor', 'floors']

    def get_record(self, dungeon):
        records = dungeon.chara_records.all()
        if len(records) == 0:
            return None
        return CharaUGCDungeonRecordSerializer(records[0]).data
