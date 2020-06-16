from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin
from rest_framework.response import Response

from chara.serializers import CharaIntroductionSerializer, SendMoneySerializer


class CharaIntroductionView(BaseGenericAPIView):
    serializer_class = CharaIntroductionSerializer

    def put(self, request, chara_id):
        chara = self.get_chara()
        serializer = self.get_serializer(chara.introduction, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    def get(self, request, chara_id):
        chara = self.get_chara()
        serializer = self.get_serializer(chara.introduction)

        return Response(serializer.data)


class SendMoneyView(BaseGenericAPIView):
    serializer_class = SendMoneySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})
