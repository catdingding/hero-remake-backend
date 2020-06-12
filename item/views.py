from django.db.models import Q
from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin
from rest_framework.response import Response

from item.serializers import UseItemSerializer, SendItemSerializer


class UseItemView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = UseItemSerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response({'detail': result})


class SendItemView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = SendItemSerializer

    def post(self, request, chara_id):
        chara = self.get_chara()
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response({'status': 'success'})
