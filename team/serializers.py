import serpy
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer, SerpyModelSerializer

from battle.models import Dungeon
from chara.models import Chara
from item.models import Item
from team.models import Team, TeamJoinRequest, TeamDungeonRecord
from battle.serializers import DungeonSerializer
from chara.serializers import CharaSimpleSerializer

from system.utils import push_log, send_private_message_by_system


class TeamDungeonRecordSerializer(SerpyModelSerializer):
    dungeon = DungeonSerializer()

    class Meta:
        model = TeamDungeonRecord
        fields = ['id', 'dungeon', 'status', 'current_floor', 'passed_times']


class TeamProfileSerializer(SerpyModelSerializer):
    leader = CharaSimpleSerializer()
    members = CharaSimpleSerializer(many=True)
    member_count = serpy.Field()

    dungeon_records = TeamDungeonRecordSerializer(many=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'leader', 'members', 'member_count', 'dungeon_records']


class FoundTeamSerializer(BaseModelSerializer):
    class Meta:
        model = Team
        fields = ['name']

    def save(self):
        team = Team.objects.create(name=self.validated_data['name'], leader=self.chara)
        TeamDungeonRecord.objects.bulk_create([TeamDungeonRecord(team=team, dungeon=x) for x in Dungeon.objects.all()])
        self.chara.team = team
        self.chara.save()

        TeamJoinRequest.objects.filter(chara=self.chara).delete()

        push_log("隊伍", f"{self.chara.name}建立了{team.name}")

    def validate(self, data):
        if self.chara.team is not None:
            raise serializers.ValidationError("已有隊伍")
        return data


class TeamJoinRequestSerializer(SerpyModelSerializer):
    chara = CharaSimpleSerializer()

    class Meta:
        model = TeamJoinRequest
        fields = ['id', 'chara', 'created_at']


class TeamJoinRequestCreateSerializer(BaseModelSerializer):
    class Meta:
        model = TeamJoinRequest
        fields = ['team']

    def create(self, validated_data):
        team = validated_data['team']
        join_request = TeamJoinRequest.objects.create(chara=self.chara, team=team)

        send_private_message_by_system(self.chara.id, team.leader_id, f"{self.chara.name}發出了入隊申請")

        return join_request

    def validate(self, data):
        if self.chara.team:
            raise serializers.ValidationError("已有所屬隊伍")
        if TeamJoinRequest.objects.filter(chara=self.chara, team=data['team']).exists():
            raise serializers.ValidationError("已提出過申請")
        return data


class TeamJoinRequestReviewSerializer(BaseSerializer):
    action = serializers.ChoiceField(choices=['accept', 'reject'])

    def save(self):
        chara = self.instance.chara.lock()

        if self.validated_data['action'] == 'accept':
            if chara.team:
                raise serializers.ValidationError("該角色已加入隊伍")

            chara.team = self.team
            chara.save()

            TeamJoinRequest.objects.filter(chara=chara).delete()

            push_log("隊伍", f"{chara.name}加入了{self.team.name}")

            return {'display_message': '入隊申請已通過'}

        elif self.validated_data['action'] == 'reject':
            self.instance.delete()
            return {'display_message': '入隊申請已拒絕'}

    def validate(self, data):
        if self.team.members.count() >= 3:
            raise serializers.ValidationError("隊伍已滿")
        return data


class LeaveTeamSerializer(BaseSerializer):
    def save(self):
        team = self.chara.team

        self.chara.team = None
        self.chara.save()

        push_log("隊伍", f"{self.chara.name}離開了{team.name}")

    def validate(self, data):
        if self.chara.team is None:
            raise serializers.ValidationError("無隊伍角色無法離開隊伍")
        if self.chara.team.leader == self.chara:
            raise serializers.ValidationError("隊長無法離開隊伍")
        return data


class DismissTeamMemberSerializer(BaseSerializer):
    chara = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    def save(self):
        chara = self.validated_data['chara']

        chara.team = None
        chara.save()

    def validate_chara(self, chara):
        chara = chara.lock()
        if chara.team != self.team:
            raise serializers.ValidationError("不可開除其他隊伍的角色")
        if self.team.leader == chara:
            raise serializers.ValidationError("無法開除隊長")
        return chara


class DisbandTeamSerializer(BaseSerializer):
    def save(self):
        Chara.objects.filter(team=self.team).update(team=None)
        self.team.delete()


class ChangeTeamDungeonRecordStatusSerializer(BaseSerializer):
    record = serializers.PrimaryKeyRelatedField(queryset=TeamDungeonRecord.objects.all())
    new_status = serializers.ChoiceField(choices=['inactive', 'active'])

    def save(self):
        new_status = self.validated_data['new_status']
        record = self.validated_data['record']
        dungeon = record.dungeon

        if new_status == 'active':
            if dungeon.ticket_type_id:
                self.chara.lose_items(
                    'bag', [Item(type_id=dungeon.ticket_type_id, number=dungeon.ticket_cost)]
                )

            record.status = new_status
            record.save()
        elif new_status == 'inactive':
            gold = dungeon.gold_reward_per_floor * record.current_floor

            loots = []
            for reward in dungeon.rewards.all():
                for i in range(record.current_floor // reward.divisor * reward.number):
                    loots.extend(reward.group.pick())

            if not loots and not gold:
                reward_message = "一些……嗯……寶貴的探索體驗"
            else:
                reward_message = f"{gold}金錢" + ('與' + '、'.join(f'{x.name}*{x.number}' for x in loots)) if loots else ""

            if not dungeon.is_infinite and record.current_floor == dungeon.max_floor:
                message = f"{self.team.name}探索{dungeon.name}成功，在地城深處獲得了{reward_message}"
            else:
                message = f"{self.team.name}在探索{dungeon.name}第{record.current_floor}層時被迫撤退，途中獲得了{reward_message}"

            push_log("地城", message)
            for chara in self.team.members.all():
                if chara != self.chara:
                    send_private_message_by_system(self.team.leader_id, chara.id, message)

            self.chara.get_items('bag', loots)

            self.chara.gold += gold
            self.chara.save()

            record.status = new_status
            record.current_floor = 0
            record.save()

            return {'display_message': f"獲得了{reward_message}"}

    def validate_record(self, record):
        if record.team != self.team:
            raise serializers.ValidationError("隊伍錯誤")
        return record

    def validate(self, data):
        if (data['new_status'] == 'active' and data['record'].status != 'inactive') or \
                (data['new_status'] == 'inactive' and data['record'].status != 'ended'):
            raise serializers.ValidationError("地城狀態錯誤")
        return data


class ChangeLeaderSerializer(BaseSerializer):
    chara = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    def save(self):
        chara = self.validated_data['chara']

        self.team.leader = chara
        self.team.save()

    def validate_chara(self, chara):
        if chara.team != self.team:
            raise serializers.ValidationError("不可指派給其他隊伍的角色")
        if chara == self.chara:
            raise serializers.ValidationError("……指派給自己？")
        return chara
