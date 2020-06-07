from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin
from rest_framework.response import Response

from ability.serializers import LearnAbilitySerializer


class LearnAbilityView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = LearnAbilitySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})
