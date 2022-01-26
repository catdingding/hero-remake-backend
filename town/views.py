from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaPostViewMixin

from town.serializers import InnSleepSerializer, ChangeNameSerializer, AltarSubmitSerializer


class InnSleepView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = InnSleepSerializer
    check_in_town = True


class ChangeNameView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = ChangeNameSerializer
    check_in_town = True


class AltarSubmitView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = AltarSubmitSerializer
    check_in_town = True
