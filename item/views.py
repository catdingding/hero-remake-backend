from django.db.models import Q
from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.response import Response

from item.serializers import UseItemSerializer, SendItemSerializer, StorageTakeSerializer, StoragePutSerializer


class UseItemView(BaseGenericAPIView):
    serializer_class = UseItemSerializer

    def post(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response({'detail': result})


class SendItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SendItemSerializer
    LOCK_CHARA = False


class StorageTakeView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = StorageTakeSerializer


class StoragePutView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = StoragePutSerializer
