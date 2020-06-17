from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.response import Response

from chara.serializers import (
    CharaIntroductionSerializer, SendMoneySerializer, SlotEquipSerializer, SlotDivestSerializer
)


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


class SendMoneyView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SendMoneySerializer


class SlotEquipView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SlotEquipSerializer


class SlotDivestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SlotDivestSerializer
