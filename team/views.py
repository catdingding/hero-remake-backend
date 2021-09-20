from django.db.models import Count

from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaPostViewMixin, TeamPostViewMixin
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, DestroyModelMixin, CreateModelMixin

from team.models import Team, TeamJoinRequest
from team.serializers import (
    TeamProfileSerializer, FoundTeamSerializer,
    TeamJoinRequestReviewSerializer, LeaveTeamSerializer, TeamJoinRequestSerializer,
    TeamJoinRequestCreateSerializer, DismissTeamMemberSerializer, DisbandTeamSerializer,
    ChangeTeamDungeonRecordStatusSerializer
)


class TeamViewSet(ListModelMixin, RetrieveModelMixin, BaseGenericViewSet):
    serializer_class = TeamProfileSerializer
    queryset = Team.objects.annotate(member_count=Count('members')).select_related('leader').all()


class FoundTeamView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = FoundTeamSerializer


class LeaveTeamView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = LeaveTeamSerializer


class TeamJoinRequestViewSet(BaseGenericViewSet):
    queryset = TeamJoinRequest.objects.all()
    serializer_class = TeamJoinRequestSerializer
    serializer_action_classes = {
        'create': TeamJoinRequestCreateSerializer,
        'review': TeamJoinRequestReviewSerializer,
    }

    def create(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'display_message': '入隊申請已發送'})

    def list(self, request):
        team = self.get_team(role='leader')
        queryset = self.get_queryset().filter(team=team)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def review(self, request, pk):
        team = self.get_team(role='leader', lock=True)
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)


class DismissTeamMemberView(TeamPostViewMixin, BaseGenericAPIView):
    serializer_class = DismissTeamMemberSerializer
    role = 'leader'


class DisbandTeamView(TeamPostViewMixin, BaseGenericAPIView):
    serializer_class = DisbandTeamSerializer
    role = 'leader'


class ChangeTeamDungeonRecordStatusView(TeamPostViewMixin, BaseGenericAPIView):
    serializer_class = ChangeTeamDungeonRecordStatusSerializer
    role = 'leader'
