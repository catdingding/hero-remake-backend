from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from battle.models import Dungeon
from chara.models import Chara
from team.models import Team, TeamJoinRequest, TeamDungeonRecord
from battle.serializers import DungeonSerializer
from chara.serializers import CharaSimpleSerializer

from system.utils import push_log, send_private_message_by_system


class TeamDungeonRecordSerializer(BaseModelSerializer):
    dungeon = DungeonSerializer()

    class Meta:
        model = TeamDungeonRecord
        fields = ['id', 'dungeon', 'current_floor', 'passed_times']


class TeamProfileSerializer(BaseModelSerializer):
    leader = CharaSimpleSerializer()
    members = CharaSimpleSerializer(many=True)
    member_count = serializers.IntegerField()

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


class TeamJoinRequestSerializer(BaseModelSerializer):
    chara = CharaSimpleSerializer(read_only=True)

    class Meta:
        model = TeamJoinRequest
        fields = ['id', 'chara', 'team', 'created_at']
        read_only_fields = ['id', 'chara', 'created_at']
        extra_kwargs = {'team': {'write_only': True}}

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
