from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer, SerpyModelSerializer

from ugc.models import (
    UGCMonster, UGCMonsterAttribute, UGCMonsterSkillSetting,
    UGCDungeon, UGCDungeonFloor, UGCDungeonFloorMonster
)


class UGCMonsterSkillSettingSerializer(BaseModelSerializer):
    class Meta:
        model = UGCMonsterSkillSetting
        fields = ['skill', 'hp_percentage', 'mp_percentage',
                  'defender_hp_percentage', 'defender_mp_percentage', 
                  'times_limit', 'probability']


class UGCMonsterAttributeSerializer(BaseModelSerializer):
    class Meta:
        model = UGCMonsterAttribute
        fields = ['type', 'value']


class UGCMonsterModifySerializer(BaseModelSerializer):
    hp = serializers.IntegerField(min_value=1)
    mp = serializers.IntegerField(min_value=1)

    attributes = UGCMonsterAttributeSerializer(many=True)
    skill_settings = UGCMonsterSkillSettingSerializer(many=True)

    class Meta:
        model = UGCMonster
        fields = ['name', 'element_type', 'hp', 'mp', 'abilities', 'attributes', 'skill_settings']
        extra_kwargs = {'abilities': {'allow_empty': True}}

    def save(self):
        attributes, skill_settings = [
            self.validated_data.pop(x) for x in ['attributes', 'skill_settings']
        ]

        if self.instance is not None:
            monster = self.instance
            self.update(monster, self.validated_data)
            monster.attributes.all().delete()
            monster.skill_settings.all().delete()
        else:
            self.validated_data['chara'] = self.chara
            monster = self.create(self.validated_data)

        UGCMonsterAttribute.objects.bulk_create([
            UGCMonsterAttribute(monster=monster, **attribute)
            for attribute in attributes
        ])
        UGCMonsterSkillSetting.objects.bulk_create([
            UGCMonsterSkillSetting(monster=monster, order=i, **setting)
            for i, setting in enumerate(skill_settings)
        ])

    def validate(self, data):
        if self.instance is None and UGCMonster.objects.filter(chara=self.chara).count() >= 10:
            raise serializers.ValidationError("最多僅可創建10種怪物")
        return data

    def validate_abilities(self, abilities):
        if len(abilities) > 10:
            raise serializers.ValidationError("最多可設置10項奧義")
        return abilities

    def validate_skill_settings(self, settings):
        if len(settings) > 10:
            raise serializers.ValidationError("不可設定超過10項技能")
        return settings

    def validate_attributes(self, attributes):
        if len(set(x['type'] for x in attributes)) != 6:
            raise serializers.ValidationError("能力設置錯誤")
        return attributes


class UGCDungeonFloorMonsterSerializer(BaseModelSerializer):
    class Meta:
        model = UGCDungeonFloorMonster
        fields = ['monster']


class UGCDungeonFloorSerializer(BaseModelSerializer):
    monsters = UGCDungeonFloorMonsterSerializer(many=True)

    class Meta:
        model = UGCDungeonFloor
        fields = ['monsters']


class UGCDungeonModifySerializer(BaseModelSerializer):
    floors = UGCDungeonFloorSerializer(many=True)

    class Meta:
        model = UGCDungeon
        fields = ['name', 'description', 'floors']

    def save(self):
        floors = self.validated_data.pop('floors')

        if self.instance is not None:
            dungeon = self.instance
            self.update(dungeon, self.validated_data)
            dungeon.floors.all().delete()
        else:
            self.validated_data['chara'] = self.chara
            dungeon = self.create(self.validated_data)

        for i, floor_data in enumerate(floors):
            monsters = floor_data.pop('monsters')
            floor = UGCDungeonFloor.objects.create(dungeon=dungeon, floor=i + 1, **floor_data)
            UGCDungeonFloorMonster.objects.bulk_create([
                UGCDungeonFloorMonster(dungeon_floor=floor, **monster)
                for monster in monsters
            ])

    def validate(self, data):
        if self.instance is None and UGCDungeon.objects.filter(chara=self.chara).count() >= 2:
            raise serializers.ValidationError("最多僅可創建2個地城")
        data['max_floor'] = len(data['floors'])
        return data

    def validate_floors(self, floors):
        if len(floors) == 0:
            raise serializers.ValidationError("請設定至少1層")
        if len(floors) >= 10:
            raise serializers.ValidationError("不可超過10層")
        for floor in floors:
            if len(floor['monsters']) > 3:
                raise serializers.ValidationError("每層不可超過3隻怪物")
            for monster in floor['monsters']:
                if monster['monster'].chara_id != self.chara.id:
                    raise serializers.ValidationError("不可使用別人的怪物")
        return floors
