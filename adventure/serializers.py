import random
import serpy
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer, SerpyModelSerializer
from battle.battle import Battle

from adventure.models import Adventure, AdventureBattle, AdventureEvent, AdventureRecord, AdventureStep
from adventure.event_effects import EVENT_EFFECT_CLASSES

from ability.serializers import AbilitySerializer
from asset.serializers import SceneSerializer
from battle.serializers import MonsterSerializer


class AdventureBattleSerializer(SerpyModelSerializer):
    monsters = MonsterSerializer(many=True)

    class Meta:
        model = AdventureBattle
        fields = ['name', 'description', 'monsters']


class AdventureEventSerializer(SerpyModelSerializer):
    class Meta:
        model = AdventureEvent
        fields = ['name', 'description', 'chooser']


class AdventureRecordSerializer(SerpyModelSerializer):
    abilities = AbilitySerializer(fields=['name'], many=True)

    class Meta:
        model = AdventureRecord
        fields = ['status', 'current_step', 'difficulty', 'abilities']


class AdventureStepSerializer(SerpyModelSerializer):
    battle = AdventureBattleSerializer(fields=['name', 'description'])
    event = AdventureEventSerializer(fields=['name', 'description'])
    scene = SceneSerializer(fields=['name', 'description'])

    class Meta:
        model = AdventureStep
        fields = ['step', 'name', 'type', 'battle', 'event', 'scene', 'description']


class AdventureSerializer(SerpyModelSerializer):
    record = serpy.MethodField()

    class Meta:
        model = Adventure
        fields = ['id', 'name', 'cost', 'max_step', 'record']

    def get_record(self, dungeon):
        records = dungeon.records.all()
        if len(records) == 0:
            return None
        return AdventureRecordSerializer(records[0]).data


class AdventureProfileSerializer(AdventureSerializer):
    steps = AdventureStepSerializer(many=True)
    abilities = AbilitySerializer(many=True)

    class Meta:
        model = Adventure
        fields = ['id', 'name', 'cost', 'max_step', 'record', 'steps', 'abilities']


class AdventureStartSerializer(BaseSerializer):
    def save(self):
        new_status = 'active'
        adventure = self.instance

        record, _ = AdventureRecord.objects.get_or_create(chara=self.chara, adventure=adventure)
        if record.status != 'inactive':
            raise serializers.ValidationError("冒險狀態錯誤")

        record.current_step = 0
        record.status = new_status
        record.save()


class AdventureTerminateSerializer(BaseSerializer):
    def save(self):
        adventure = self.instance
        record, _ = AdventureRecord.objects.get_or_create(chara=self.chara, adventure=adventure)
        if record.status != 'ended' and record.current_step != adventure.max_step:
            raise serializers.ValidationError("冒險狀態錯誤")

        record.status = 'inactive'
        record.current_step = 0
        record.abilities.clear()
        record.save()

        return {'display_message': f"冒險已結束"}


class AdventureProcessBattleSerializer(BaseSerializer):
    def save(self):
        adventure = self.instance
        adventure_record = AdventureRecord.objects.get(chara=self.chara, adventure=adventure)

        if adventure_record.status != 'active':
            raise serializers.ValidationError("冒險狀態錯誤")

        step_number = adventure_record.current_step + 1
        adventure_battle = AdventureStep.objects.get(adventure=adventure, step=step_number).battle

        if not adventure_battle:
            raise serializers.ValidationError("冒險狀態錯誤")

        battle = Battle(
            attackers=[self.chara], defenders=adventure_battle.monsters.all(), battle_type='adventure',
            context={'adventure_abilities': adventure_record.abilities.all()}
        )
        battle.execute()
        win = (battle.winner == 'attacker')

        if win:
            adventure_record.current_step = step_number

        if not win:
            adventure_record.status = 'ended'

        result = {
            'winner': battle.winner,
            'logs': battle.logs,
            'messages': [f"{adventure.name}-{step_number}"]
        }

        adventure_record.save()

        return result


class AdventureProcessEventSerializer(BaseSerializer):
    def save(self):
        adventure = self.instance
        adventure_record = AdventureRecord.objects.get(chara=self.chara, adventure=adventure)

        if adventure_record.status != 'active':
            raise serializers.ValidationError("冒險狀態錯誤")

        step_number = adventure_record.current_step + 1
        event = AdventureStep.objects.get(adventure=adventure, step=step_number).event

        if not event:
            raise serializers.ValidationError("冒險狀態錯誤")

        if event.chooser == 'random':
            effect = random.choice(event.candidate_effects.all())
        else:
            raise NotImplemented()

        effect_processor = EVENT_EFFECT_CLASSES[effect.type_id](effect, self.chara, adventure_record)
        message = effect_processor.execute()

        adventure_record.current_step = step_number
        adventure_record.save()

        return {"display_message": message}


class AdventureProcessSceneSerializer(BaseSerializer):
    def save(self):
        adventure = self.instance
        adventure_record = AdventureRecord.objects.get(chara=self.chara, adventure=adventure)

        if adventure_record.status != 'active':
            raise serializers.ValidationError("冒險狀態錯誤")

        step_number = adventure_record.current_step + 1
        scene = AdventureStep.objects.get(adventure=adventure, step=step_number).scene

        if not scene:
            raise serializers.ValidationError("冒險狀態錯誤")

        adventure_record.current_step = step_number
        adventure_record.save()

        return SceneSerializer(scene).data
