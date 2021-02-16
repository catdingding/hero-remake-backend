from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaViewMixin, CharaPostViewMixin
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from world.serializers import MoveSerializer, LocationSerializer, MapQuerySerializer, ElementTypeSerializer
from world.models import Location, ElementType


class MoveView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = MoveSerializer
    check_next_action_time = True


class MapView(BaseGenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LocationSerializer

    def get(self, request):
        param_serializer = MapQuerySerializer(data=request.query_params)
        param_serializer.is_valid(raise_exception=True)

        x, y, radius = (param_serializer.validated_data[x] for x in ['x', 'y', 'radius'])
        locations = Location.objects.filter(x__gte=x - radius, x__lte=x + radius, y__gte=y - radius, y__lte=y + radius)
        locations = locations.order_by('-y', 'x').select_related('battle_map', 'town')

        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)


class ElementTypeView(ListModelMixin, BaseGenericAPIView):
    permission_classes = [AllowAny]
    queryset = ElementType.objects.all()
    serializer_class = ElementTypeSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
