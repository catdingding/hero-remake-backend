from django.db.models import F

from rest_framework import serializers

from battle.models import BattleMap
from chara.models import Chara
from base.serializers import BaseSerializer, BaseModelSerializer
from battle.battle_map_processors import BATTLE_MAP_PROCESSORS
from battle.battle import Battle


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


class PvPFightSerializer(BaseSerializer):
    opponent = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    def save(self):
        chara, opponent = Chara.objects.lock_by_pks(pks=[self.chara.id, self.validated_data['opponent'].id])

        battle = Battle(attackers=[self.chara], defenders=[opponent], battle_type='pvp')

        battle.execute()
        win = (battle.winner == 'attacker')

        points = (opponent.pvp_points - chara.pvp_points) // 10
        if win:
            points = max(1 if points == 0 else points, 0)
        else:
            points = min(points, -1)

        chara.pvp_points += points
        chara.set_next_action_time()
        chara.save()

        opponent.pvp_points -= points
        opponent.save()

        return {
            'winner': battle.winner,
            'logs': battle.logs,
            'messages': [f"PvP點數{points if points < 0 else f'+{points}' }"]
        }
