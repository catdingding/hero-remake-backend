from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaProcessPayloadViewMixin
from django.db.models import Prefetch
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.mixins import (
    ListModelMixin, RetrieveModelMixin, DestroyModelMixin
)
from base.pagination import BasePagination

from adventure.models import Adventure, AdventureStep, AdventureRecord
from adventure.serializers import (
    AdventureSerializer, AdventureProfileSerializer, AdventureEventSerializer,
    AdventureStartSerializer, AdventureTerminateSerializer,
    AdventureProcessBattleSerializer, AdventureProcessEventSerializer, AdventureProcessSceneSerializer
)


class AdventureViewSet(
    CharaProcessPayloadViewMixin,
    ListModelMixin, RetrieveModelMixin,
    DestroyModelMixin, BaseGenericViewSet
):
    serializer_class = AdventureSerializer
    serializer_action_classes = {
        'retrieve': AdventureProfileSerializer,
        'start': AdventureStartSerializer,
        'terminate': AdventureTerminateSerializer,
        'process_battle': AdventureProcessBattleSerializer,
        'process_event': AdventureProcessEventSerializer,
        'process_scene': AdventureProcessSceneSerializer,
    }

    queryset = Adventure.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.prefetch_related(
                Prefetch('records', AdventureRecord.objects.filter(chara=self.get_chara())),
                Prefetch('steps', AdventureStep.objects.order_by('step')),
            )
        return queryset

    @action(methods=['POST'], detail=True, with_instance=True)
    def start(self, request, pk):
        return self.process_payload(request)

    @action(methods=['POST'], detail=True, with_instance=True)
    def terminate(self, request, pk):
        return self.process_payload(request)

    @action(methods=['POST'], detail=True, with_instance=True, url_path='process-battle')
    def process_battle(self, request, pk):
        return self.process_payload(request)

    @action(methods=['POST'], detail=True, with_instance=True, url_path='process-event')
    def process_event(self, request, pk):
        return self.process_payload(request)

    @action(methods=['POST'], detail=True, with_instance=True, url_path='process-scene')
    def process_scene(self, request, pk):
        return self.process_payload(request)
