from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, DestroyModelMixin, CreateModelMixin
from rest_framework.filters import SearchFilter

from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaPostViewMixin, TeamPostViewMixin

from battle.models import BattleMap, BattleResult
from battle.serializers import BattleMapFightSerializer, PvPFightSerializer, DungeonFightSerializer, BattleResultSerializer


class BattleMapViewSet(BaseGenericViewSet):
    queryset = BattleMap.objects.all()
    serializer_action_classes = {
        'fight': BattleMapFightSerializer,
    }

    @action(methods=['post'], detail=True, check_next_action_time=True)
    def fight(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result)


class PvPFightView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = PvPFightSerializer
    check_next_action_time = True
    LOCK_CHARA = False


class DungeonFightView(TeamPostViewMixin, BaseGenericAPIView):
    serializer_class = DungeonFightSerializer
    role = 'leader'


class BattleResultViewSet(ListModelMixin, RetrieveModelMixin, BaseGenericViewSet):
    serializer_class = BattleResultSerializer
    queryset = BattleResult.objects.all()

    filter_backends = [SearchFilter]
    search_fields = ['title']

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset()).order_by('-created_at')[:200]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
