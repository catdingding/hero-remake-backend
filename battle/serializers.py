import math
from django.db.models import F

from rest_framework import serializers

from battle.models import BattleMap, Dungeon, DungeonFloor, BattleResult
from chara.models import Chara
from team.models import TeamDungeonRecord
from base.serializers import BaseSerializer, BaseModelSerializer, SerpyModelSerializer
from item.serializers import ItemTypeSerializer
from battle.battle_map_processors import BATTLE_MAP_PROCESSORS
from battle.battle import Battle


class BattleMapSerializer(SerpyModelSerializer):
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


class DungeonSerializer(SerpyModelSerializer):
    ticket_type = ItemTypeSerializer(fields=['name'])

    class Meta:
        model = Dungeon
        fields = ['id', 'name', 'description', 'is_infinite', 'max_floor', 'ticket_type', 'ticket_cost']


class DungeonFightSerializer(BaseSerializer):
    dungeon = serializers.PrimaryKeyRelatedField(queryset=Dungeon.objects.all())

    def save(self):
        dungeon = self.validated_data['dungeon']
        team = self.team
        dungeon_record = TeamDungeonRecord.objects.get(dungeon=dungeon, team=team)

        if dungeon_record.status != 'active':
            raise serializers.ValidationError("地城狀態錯誤")

        floor_number = dungeon_record.current_floor + 1
        difficulty = 1
        if dungeon.is_infinite:
            difficulty = 1.02**dungeon_record.current_floor

        dungeon_floor = DungeonFloor.objects.get(
            dungeon=dungeon, floor=floor_number % dungeon.max_floor or dungeon.max_floor)

        battle = Battle(attackers=team.members.all(), defenders=[x.monster for x in dungeon_floor.monsters.all()],
                        battle_type='dungeon', difficulty=difficulty)
        battle.execute()
        win = (battle.winner == 'attacker')

        if win:
            dungeon_record.current_floor = floor_number

        if not win or (not dungeon.is_infinite and dungeon_record.current_floor == dungeon.max_floor):
            dungeon_record.status = 'ended'

            if win or dungeon.is_infinite:
                dungeon_record.passed_times += 1

        result = {
            'winner': battle.winner,
            'logs': battle.logs,
            'messages': []
        }

        dungeon_record.save()

        BattleResult.objects.create(title=f"{team.name}-{dungeon.name}-{floor_number}層", content=result)

        return result


class BattleResultSerializer(SerpyModelSerializer):
    class Meta:
        model = BattleResult
        fields = ['id', 'title', 'content', 'created_at']
