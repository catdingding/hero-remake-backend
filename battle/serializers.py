import json
from django.db.models import F

from rest_framework import serializers

from battle.models import BattleMap, Dungeon, DungeonFloor, BattleResult
from chara.models import Chara
from team.models import TeamDungeonRecord
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


class DungeonSerializer(BaseModelSerializer):
    class Meta:
        model = Dungeon
        fields = ['id', 'name', 'description', 'max_floor']


class DungeonFightSerializer(BaseSerializer):
    dungeon = serializers.PrimaryKeyRelatedField(queryset=Dungeon.objects.all())

    def save(self):
        dungeon = self.validated_data['dungeon']
        team = self.team
        dungeon_record = TeamDungeonRecord.objects.get(dungeon=dungeon, team=team)
        dungeon_floor = DungeonFloor.objects.get(dungeon=dungeon, floor=dungeon_record.current_floor + 1)

        battle = Battle(attackers=team.members.all(), defenders=dungeon_floor.monsters.all(), battle_type='dungeon')
        battle.execute()
        win = (battle.winner == 'attacker')

        if win:
            dungeon_record.current_floor += 1

        if dungeon_record.current_floor == dungeon.max_floor:
            dungeon_record.current_floor = 0
            dungeon_record.passed_times += 1

        result = {
            'winner': battle.winner,
            'logs': battle.logs,
            'messages': []
        }

        dungeon_record.save()

        BattleResult.objects.create(title=f"{team.name}-{dungeon.name}-{dungeon_floor.floor}層", content=result)

        return result


class BattleResultSerializer(BaseModelSerializer):
    class Meta:
        model = BattleResult
        fields = ['id', 'title', 'content', 'created_at']
