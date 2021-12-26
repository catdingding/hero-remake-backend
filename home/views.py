from base.views import BaseGenericAPIView, CharaPostViewMixin, BaseGenericViewSet

from home.serializers import (
    CharaFarmExpandSerializer, CharaFarmPlaceItemSerializer, CharaFarmRemoveItemSerializer,
    CharaFarmHarvestSerializer
)


class CharaFarmExpandView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaFarmExpandSerializer


class CharaFarmPlaceItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaFarmPlaceItemSerializer


class CharaFarmRemoveItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaFarmRemoveItemSerializer


class CharaFarmHarvestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaFarmHarvestSerializer
