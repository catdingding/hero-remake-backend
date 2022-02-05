from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaProcessPayloadViewMixin
from django.db.models import Prefetch
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.mixins import (
    ListModelMixin, RetrieveModelMixin, DestroyModelMixin
)
from base.pagination import BasePagination

from ugc.models import UGCMonster, UGCDungeon, CharaUGCDungeonRecord
from ugc.serializers import (
    UGCMonsterSerializer, UGCMonsterModifySerializer, UGCDungeonSerializer, UGCDungeonModifySerializer,
    ChangeCharaUGCDungeonRecordStatusSerializer, CharaUGCDungeonFightSerializer
)


class UGCMonsterViewSet(
    CharaProcessPayloadViewMixin,
    ListModelMixin, RetrieveModelMixin,
    DestroyModelMixin, BaseGenericViewSet
):
    serializer_class = UGCMonsterSerializer
    serializer_action_classes = {
        'create': UGCMonsterModifySerializer,
        'update': UGCMonsterModifySerializer,
        'retrieve': UGCMonsterModifySerializer
    }

    queryset = UGCMonster.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['chara']

    pagination_class = BasePagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['destroy', 'update']:
            queryset = queryset.filter(chara=self.get_chara(lock=True))
        elif self.action in ['list']:
            queryset = queryset.select_related('chara', 'element_type').prefetch_related(
                'abilities', 'skill_settings', 'attributes'
            )
        return queryset

    def create(self, request):
        return self.process_payload(request)

    def update(self, request, pk):
        self.with_instance = True
        return self.process_payload(request)


class UGCDungeonViewSet(
    CharaProcessPayloadViewMixin,
    ListModelMixin, RetrieveModelMixin,
    DestroyModelMixin, BaseGenericViewSet
):
    serializer_class = UGCDungeonSerializer
    serializer_action_classes = {
        'create': UGCDungeonModifySerializer,
        'update': UGCDungeonModifySerializer,
        'retrieve': UGCDungeonModifySerializer,
        'change_record_status': ChangeCharaUGCDungeonRecordStatusSerializer,
        'fight': CharaUGCDungeonFightSerializer
    }

    queryset = UGCDungeon.objects.all()

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['chara']

    pagination_class = BasePagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['destroy', 'update']:
            queryset = queryset.filter(chara=self.get_chara(lock=True))
        elif self.action in ['list']:
            queryset = queryset.select_related('chara').prefetch_related(
                'floors__monsters',
                Prefetch('chara_records', CharaUGCDungeonRecord.objects.filter(chara=self.get_chara()))
            )
        return queryset

    def create(self, request):
        return self.process_payload(request)

    def update(self, request, pk):
        self.with_instance = True
        return self.process_payload(request)

    @action(methods=['POST'], detail=True, url_path='change-record-status', with_instance=True)
    def change_record_status(self, request, pk):
        return self.process_payload(request)

    @action(methods=['POST'], detail=True, with_instance=True)
    def fight(self, request, pk):
        return self.process_payload(request)
