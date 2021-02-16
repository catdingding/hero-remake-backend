from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaPostViewMixin

from town.serializers import InnSleepSerializer


class InnSleepView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = InnSleepSerializer
    check_in_town = True
