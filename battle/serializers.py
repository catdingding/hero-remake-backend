from django.db.models import F

from rest_framework import serializers

from battle.models import BattleMap
from base.serializers import BaseSerializer, BaseModelSerializer
from battle.battle_map_processors import BATTLE_MAP_PROCESSORS


class BattleMapSerializer(BaseModelSerializer):
    class Meta:
        model = BattleMap
        fields = ['id', 'name']


class BattleMapFightSerializer(BaseSerializer):
    def save(self):
        battle_map = self.instance
        chara = self.chara

        if battle_map.need_ticket:
            affected_rows = chara.battle_map_tickets.filter(
                battle_map=battle_map, value__gt=0).update(value=F('value') - 1)
            if affected_rows == 0:
                raise serializers.ValidationError("無法進入該地圖")

        processor_class = BATTLE_MAP_PROCESSORS[battle_map.id]
        processor = processor_class(chara, battle_map)

        chara.set_next_action_time()
        chara.save()

        return processor.execute()
