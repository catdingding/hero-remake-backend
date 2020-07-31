from django.db.models import Q
from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.response import Response

from item.serializers import (
    UseItemSerializer, SendItemSerializer, StorageTakeSerializer, StoragePutSerializer,
    SmithUpgradeSerializer, SmithReplaceAbilitySerializer
)


class UseItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = UseItemSerializer


class SendItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SendItemSerializer
    LOCK_CHARA = False


class StorageTakeView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = StorageTakeSerializer


class StoragePutView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = StoragePutSerializer


class SmithUpgradeView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SmithUpgradeSerializer


class SmithReplaceAbilityView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SmithReplaceAbilitySerializer
