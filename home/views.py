from base.views import BaseGenericAPIView, CharaPostViewMixin, BaseGenericViewSet

from home.serializers import CharaFarmExpandSerializer, CharaFarmPlaceItemSerializer, CharaFarmHarvestSerializer


class CharaFarmExpandView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaFarmExpandSerializer


class CharaFarmPlaceItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaFarmPlaceItemSerializer


class CharaFarmHarvestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = CharaFarmHarvestSerializer
