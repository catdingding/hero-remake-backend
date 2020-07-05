from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import action

from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaPostViewMixin

from battle.models import BattleMap
from battle.serializers import BattleMapFightSerializer


class BattleMapViewSet(BaseGenericViewSet):
    queryset = BattleMap.objects.all()
    serializer_action_classes = {
        'fight': BattleMapFightSerializer,
    }

    @action(methods=['post'], detail=True)
    def fight(self, request, pk):
        chara = self.get_chara(lock=True, check_next_action_time=True)
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)
