from base.views import BaseGenericAPIView, CharaPostViewMixin, BaseGenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.decorators import action

from npc.models import NPC
from npc.serializers import (
    NPCSerializer, NPCProfileSerializer, NPCFavoriteSubmitSerializer, NPCExchangeOptionExchangeSerializer,
    NPCFightSerializer
)


class NPCViewSet(ListModelMixin, BaseGenericViewSet):
    queryset = NPC.objects.all().order_by('-is_admin')
    serializer_class = NPCSerializer

    @action(methods=['get'], detail=True, serializer_class=NPCProfileSerializer)
    def profile(self, request, pk):
        self.get_chara()
        npc = NPC.objects.prefetch_related(
            'abilities', 'attributes', 'skill_settings', 'favorites', 'exchange_options'
        ).select_related(
            'element_type', 'info'
        ).get(id=pk)
        serializer = self.get_serializer(npc)
        return Response(serializer.data)

    @action(methods=['post'], detail=True, serializer_class=NPCFightSerializer)
    def fight(self, request, pk):
        self.get_chara()
        serializer = self.get_serializer(self.get_object())
        result = serializer.save()
        return Response(result)


class NPCFavoriteSubmitView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = NPCFavoriteSubmitSerializer


class NPCExchangeOptionExchangeView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = NPCExchangeOptionExchangeSerializer
