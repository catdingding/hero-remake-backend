from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer, SerpyModelSerializer

from ugc.models import (
    UGCMonster, UGCMonsterAttribute, UGCMonsterSkillSetting,
    UGCDungeon, UGCDungeonFloor, UGCDungeonFloorMonster,
    CharaUGCDungeonRecord
)
from battle.models import BattleResult

from battle.battle import Battle
from system.utils import push_log


class ChangeCharaUGCDungeonRecordStatusSerializer(BaseSerializer):
    new_status = serializers.ChoiceField(choices=['inactive', 'active'])

    def save(self):
        new_status = self.validated_data['new_status']

        dungeon = self.instance
        record, _ = CharaUGCDungeonRecord.objects.get_or_create(chara=self.chara, dungeon=dungeon)

        if new_status == 'active':
            if record.status != 'inactive':
                raise serializers.ValidationError("地城狀態錯誤")
            record.start_floor = 0
            record.current_floor = 0
            record.status = new_status
            record.save()
        elif new_status == 'inactive':
            if record.status != 'ended':
                raise serializers.ValidationError("地城狀態錯誤")
            if record.current_floor == dungeon.max_floor:
                message = f"{self.chara.name}探索{dungeon.name}成功"
            else:
                message = f"{self.chara.name}在探索{dungeon.name}第{record.current_floor}層時被迫撤退"

            push_log("自訂地城", message)

            record.status = new_status
            record.start_floor = 0
            record.current_floor = 0
            record.save()


class CharaUGCDungeonFightSerializer(BaseSerializer):
    def save(self):
        dungeon = self.instance
        dungeon_record = CharaUGCDungeonRecord.objects.get(chara=self.chara, dungeon=dungeon)

        if dungeon_record.status != 'active':
            raise serializers.ValidationError("地城狀態錯誤")

        floor_number = dungeon_record.current_floor + 1
        dungeon_floor = UGCDungeonFloor.objects.get(dungeon=dungeon, floor=floor_number)

        battle = Battle(attackers=[self.chara], defenders=[x.monster for x in dungeon_floor.monsters.all()],
                        battle_type='ugc_dungeon')
        battle.execute()
        win = (battle.winner == 'attacker')

        if win:
            dungeon_record.current_floor = floor_number

        if not win or dungeon_record.current_floor == dungeon.max_floor:
            dungeon_record.status = 'ended'

        result = {
            'winner': battle.winner,
            'logs': battle.logs,
            'messages': [f"{dungeon.name}-{floor_number}層"]
        }

        dungeon_record.save()

        self.chara.set_next_action_time()
        self.chara.save()

        BattleResult.objects.create(title=f"{self.chara.name}-{dungeon.name}-{floor_number}層", content=result)

        return result
