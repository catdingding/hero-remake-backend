from base.views import BaseGenericAPIView, CharaPostViewMixin, BaseGenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action


from .models import Chara
from chara.serializers import (
    CharaIntroductionSerializer, SendGoldSerializer, SlotEquipSerializer, SlotDivestSerializer, RestSerializer,
    CharaProfileSerializer
)
from item.serializers import ItemSerializer

# charas belong to user


class UserCharaView(ListModelMixin, BaseGenericAPIView):
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


class CharaViewSet(ListModelMixin, BaseGenericViewSet):
    queryset = Chara.objects.all()
    serializer_class = CharaProfileSerializer
    serializer_fields = ['id', 'name', 'official']

    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['name']
    filterset_fields = ['id', 'country']

    @action(methods=['get'], detail=True, serializer_fields=[
        'name', 'country', 'element_type', 'job', 'level', 'slots',
        'hp', 'hp_max', 'mp', 'mp_max', 'attributes', 'introduction'
    ])
    def profile(self, request, pk):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)


class CharaStorageItemView(BaseGenericAPIView):
    serializer_class = ItemSerializer

    def get(self, request):
        chara = self.get_chara()
        serializer = self.get_serializer(chara.storage_items.all(), many=True)

        return Response(serializer.data)


class CharaIntroductionView(BaseGenericAPIView):
    serializer_class = CharaIntroductionSerializer

    def put(self, request):
        chara = self.get_chara()
        serializer = self.get_serializer(chara.introduction, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class SendGoldView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SendGoldSerializer
    LOCK_CHARA = False


class SlotEquipView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SlotEquipSerializer


class SlotDivestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SlotDivestSerializer


class RestView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = RestSerializer
