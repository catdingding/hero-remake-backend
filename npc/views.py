from base.views import BaseGenericAPIView, CharaPostViewMixin, BaseGenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.decorators import action

from npc.models import NPC
from npc.serializers import (
    NPCSerializer, NPCProfileSerializer, NPCFavoriteSubmitSerializer, NPCExchangeOptionExchangeSerializer
)


class NPCViewSet(ListModelMixin, BaseGenericViewSet):
    queryset = NPC.objects.all()
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


class NPCFavoriteSubmitView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = NPCFavoriteSubmitSerializer


class NPCExchangeOptionExchangeView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = NPCExchangeOptionExchangeSerializer
