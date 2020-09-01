from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response

from chara.serializers import (
    CharaIntroductionSerializer, SendMoneySerializer, SlotEquipSerializer, SlotDivestSerializer, RestSerializer,
    CharaProfileSerializer
)


class CharaView(ListModelMixin, BaseGenericAPIView):
    serializer_class = CharaProfileSerializer

    def get_queryset(self):
        return self.request.user.charas.all()

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(*args, fields=['id', 'name'], **kwargs)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class CharaProfileView(BaseGenericAPIView):
    serializer_class = CharaProfileSerializer

    def get(self, request):
        chara = self.get_chara()
        serializer = self.get_serializer(chara)

        return Response(serializer.data)


class CharaIntroductionView(BaseGenericAPIView):
    serializer_class = CharaIntroductionSerializer

    def put(self, request):
        chara = self.get_chara()
        serializer = self.get_serializer(chara.introduction, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    def get(self, request):
        chara = self.get_chara()
        serializer = self.get_serializer(chara.introduction)

        return Response(serializer.data)


class SendMoneyView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SendMoneySerializer


class SlotEquipView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SlotEquipSerializer


class SlotDivestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SlotDivestSerializer


class RestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = RestSerializer
