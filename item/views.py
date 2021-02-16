from django.db.models import Q
from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.response import Response

from item.serializers import (
    UseItemSerializer, SendItemSerializer, StorageTakeSerializer, StoragePutSerializer,
    SmithUpgradeSerializer, SmithReplaceAbilitySerializer, PetUpgradeSerializer
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
