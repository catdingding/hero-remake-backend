import math
import random
from django.db.models import F

from rest_framework import serializers

from battle.models import BattleMap, Dungeon, DungeonFloor, BattleResult, WorldBoss
from chara.models import Chara
from item.models import Item
from team.models import TeamDungeonRecord
from base.serializers import BaseSerializer, SerpyModelSerializer
from item.serializers import ItemTypeSerializer, ItemSerializer
from world.serializers import ElementTypeSerializer, LocationSerializer
from battle.battle_map_processors import BATTLE_MAP_PROCESSORS
from battle.battle import Battle
from system.utils import push_log


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


class WorldBossSerializer(SerpyModelSerializer):
    location = LocationSerializer()
    element_type = ElementTypeSerializer()

    class Meta:
        model = WorldBoss
        fields = ['id', 'name', 'location', 'element_type', 'hp_max', 'hp', 'mp_max', 'mp']


class WorldBossFightSerializer(BaseSerializer):
    world_boss = serializers.PrimaryKeyRelatedField(queryset=WorldBoss.objects.all())

    reward_settings = [
        {'id': 1558, 'cost': 0.01},
        {'id': 1557, 'cost': 0.25},
        {'id': 1559, 'cost': 0.5}
    ]

    def save(self):
        world_boss = self.validated_data['world_boss']
        team = self.team

        self.chara.lose_items('bag', [Item(type_id=1555, number=1)])

        battle = Battle(attackers=team.members.all(), defenders=[world_boss],
                        battle_type='world_boss', element_type=world_boss.element_type)
        battle.execute()
        win = (battle.winner == 'attacker')
        battle_world_boss = battle.find_chara_by_source(world_boss)

        self.chara.set_next_action_time(3)
        self.chara.save()

        # damage and reward
        damage = world_boss.hp - battle_world_boss.hp
        damage_ratio = damage / world_boss.hp_max

        loots = []
        for reward_setting in self.reward_settings:
            number = math.floor(damage_ratio / reward_setting['cost'])
            number += (damage_ratio % reward_setting['cost']) > random.random()
            if number > 0:
                loots.append(Item(type_id=reward_setting['id'], number=number))

        if win:
            loots.append(Item(type_id=1556, number=1))
        self.chara.get_items('bag', loots)

        # update world boss
        world_boss.hp = battle_world_boss.hp
        world_boss.mp = max(world_boss.mp_max * 0.2, battle_world_boss.mp)

        if world_boss.hp == 0:
            world_boss.is_alive = False

        world_boss.save()

        # save and return result
        result = {
            'winner': battle.winner,
            'logs': battle.logs,
            'loots': ItemSerializer(loots, fields=['name', 'number'], many=True).data,
            'messages': [f"造成了{damage}傷害({damage_ratio*100:.2f}%)"]
        }

        BattleResult.objects.create(title=f"{team.name}-{world_boss.name}", content=result)
        push_log("神獸", f"{team.name}向{world_boss.name}發起了挑戰，造成了{damage}傷害({damage_ratio*100:.2f}%)")
        if win:
            push_log("神獸", f"{world_boss.name}被{team.name}擊敗了")

        return result

    def validate_world_boss(self, world_boss):
        if not world_boss.is_alive:
            raise serializers.ValidationError("神獸已死亡")
        if world_boss.location != self.chara.location:
            raise serializers.ValidationError("神獸不在此地點")

        return world_boss.lock()
