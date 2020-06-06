from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin
from rest_framework.response import Response

from world.serializers import MoveSerializer


class MoveView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = MoveSerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True, check_next_action_time=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})
