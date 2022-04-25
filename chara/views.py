from datetime import datetime, timedelta
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils.timezone import localtime
from django.db.models import Exists, OuterRef, Subquery
from base.views import BaseGenericAPIView, CharaPostViewMixin, BaseGenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action

from base.pagination import BasePagination
from item.filters import ItemFilter

from .models import Chara, CharaAchievementType, CharaAchievement, CharaAchievementCounter
from chara.serializers import (
    SendGoldSerializer, SlotEquipSerializer, SlotDivestSerializer, RestSerializer,
    CharaProfileSerializer, CharaPublicProfileSerializer, IncreaseHPMPMaxSerializer, HandInQuestSerializer,
    CharaAvatarSerializer, CharaIntroductionUpdateSerializer, PartnerAssignSerializer,
    CharaAchievementTypeSerializer, CharaTitleSetSerializer, CharaConfigUpdateSerializer,
    CharaCustomTitleUpdateSerializer, CharaCustomTitleExpandSerializer
)
from item.serializers import ItemSerializer


# charas belong to user
class UserCharaView(ListModelMixin, BaseGenericAPIView):
    serializer_class = CharaProfileSerializer

    def get_queryset(self):
        return self.request.user.charas.all()

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(*args, fields=['id', 'name'], **kwargs)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class CharaProfileView(BaseGenericAPIView):
    serializer_class = CharaProfileSerializer

    def get(self, request):
        chara = self.get_chara()
        serializer = self.get_serializer(chara)
        return Response(serializer.data, headers={'Date': str(localtime())})

    def get_chara(self):
        chara = super().get_chara()
        return self.get_serializer_class().process_queryset(self.request, Chara.objects.all()).get(id=chara.id)


class CharaViewSet(ListModelMixin, BaseGenericViewSet):
    queryset = Chara.objects.all()
    serializer_class = CharaPublicProfileSerializer

    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend]
    ordering_fields = ['pvp_points', 'gold', 'proficiency', 'record__total_battle', 'hp_max', 'mp_max']
    search_fields = ['name']
    filterset_fields = ['id', 'country', 'team']

    pagination_class = BasePagination

    def get_queryset(self):
        return self.get_serializer_class().process_queryset(self.request, super().get_queryset())

    @action(methods=['get'], detail=True)
    def profile(self, request, pk):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    @method_decorator(cache_page(60))
    @action(methods=['get'], detail=False, pagination_class=None)
    def online(self, request):
        serializer = self.get_serializer(
            self.get_queryset().filter(updated_at__gt=datetime.now() - timedelta(minutes=10)),
            many=True
        )
        return Response(serializer.data)


class CharaStorageItemView(BaseGenericAPIView):
    serializer_class = ItemSerializer
    pagination_class = BasePagination
    filterset_class = ItemFilter

    def get(self, request):
        chara = self.get_chara()
        queryset = chara.storage_items.all().select_related(
            'type__slot_type', 'equipment__ability_1', 'equipment__ability_2',
            'equipment__element_type', 'equipment__battle_effect'
        )
        return self.list(request, queryset)


class CharaBagItemView(BaseGenericAPIView):
    serializer_class = ItemSerializer
    pagination_class = BasePagination
    filterset_class = ItemFilter

    def get(self, request):
        chara = self.get_chara()
        queryset = chara.bag_items.all().select_related(
            'type__slot_type', 'equipment__ability_1', 'equipment__ability_2', 'equipment__element_type'
        )
        return self.list(request, queryset)


class CharaIntroductionView(BaseGenericAPIView):
    serializer_class = CharaIntroductionUpdateSerializer

    def put(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara.introduction, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CharaConfigView(BaseGenericAPIView):
    serializer_class = CharaConfigUpdateSerializer

    def put(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara.config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class SendGoldView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SendGoldSerializer
    lock_chara = False


class SlotEquipView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SlotEquipSerializer


class SlotDivestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SlotDivestSerializer


class PartnerAssignView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = PartnerAssignSerializer


class RestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = RestSerializer


class IncreaseHPMPMaxView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = IncreaseHPMPMaxSerializer


class HandInQuestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = HandInQuestSerializer


class ChangeAvatarView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaAvatarSerializer


class CharaAchievementTypeView(ListModelMixin, BaseGenericAPIView):
    queryset = CharaAchievementType.objects.all().select_related('title_type')
    serializer_class = CharaAchievementTypeSerializer
    pagination_class = BasePagination

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            obtained=Exists(CharaAchievement.objects.filter(type=OuterRef('id'), chara=self.get_chara())),
            counter_value=Subquery(
                CharaAchievementCounter.objects.filter(
                    category=OuterRef('category'), chara=self.get_chara()
                ).values('value')[:1]
            )
        ).order_by('-obtained', 'id')
        return queryset

    def get(self, request):
        return self.list(request)


class CharaTitleSetView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaTitleSetSerializer


class CharaCustomTitleView(BaseGenericAPIView):
    serializer_class = CharaCustomTitleUpdateSerializer

    def put(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara.custom_title, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CharaCustomTitleExpandView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaCustomTitleExpandSerializer
