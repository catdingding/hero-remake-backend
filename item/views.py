from django.db.models import Q
from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response

from item.models import PetType, ItemType
from item.serializers import (
    UseItemSerializer, SendItemSerializer, StorageTakeSerializer, StoragePutSerializer,
    SmithUpgradeSerializer, SmithReplaceAbilitySerializer, PetUpgradeSerializer, SmithReplaceElementTypeSerializer,
    BattleMapTicketToItemSerializer, PetTypeSerializer, ToggleEquipmentLockSerializer, ItemTypeSerializer
)


class UseItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = UseItemSerializer


class SendItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SendItemSerializer
    LOCK_CHARA = False


class StorageTakeView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = StorageTakeSerializer
    check_in_town = True


class StoragePutView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = StoragePutSerializer
    check_in_town = True


class SmithUpgradeView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SmithUpgradeSerializer
    check_in_town = True


class SmithReplaceAbilityView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SmithReplaceAbilitySerializer
    check_in_town = True


class PetUpgradeView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = PetUpgradeSerializer
    check_in_town = True


class SmithReplaceElementTypeView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SmithReplaceElementTypeSerializer
    check_in_town = True


class BattleMapTicketToItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = BattleMapTicketToItemSerializer


class ToggleEquipmentLockView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = ToggleEquipmentLockSerializer


class PetTypeView(ListModelMixin, BaseGenericAPIView):
    serializer_class = PetTypeSerializer
    queryset = PetType.objects.select_related('item_type__element_type').all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ItemTypeView(ListModelMixin, BaseGenericAPIView):
    serializer_class = ItemTypeSerializer
    queryset = ItemType.objects.all()

    filter_backends = [SearchFilter]
    search_fields = ['name']

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset)[:20]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
