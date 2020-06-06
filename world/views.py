from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from world.serializers import MoveSerializer, LocationSerializer, MapQuerySerializer
from world.models import Location


class MoveView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = MoveSerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True, check_next_action_time=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class MapView(BaseGenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LocationSerializer

    def get(self, request):
        param_serializer = MapQuerySerializer(data=request.query_params)
        param_serializer.is_valid(raise_exception=True)

        x, y, radius = (param_serializer.validated_data[x] for x in ['x', 'y', 'radius'])
        locations = Location.objects.filter(x__gte=x - radius, x__lte=x + radius, y__gte=y - radius, y__lte=y + radius)
        locations = locations.select_related('battle_map', 'town')

        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)
