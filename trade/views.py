from django.db.models import Q
from django.utils.timezone import localtime
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin

from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaPostViewMixin

from trade.models import Auction, Sale, Purchase, ExchangeOption
from trade.serializers import (
    AuctionSerializer, AuctionCreateSerializer, AuctionBidSerializer,
    AuctionReceiveItemSerializer, AuctionReceiveGoldSerializer,
    SaleSerializer, SaleCreateSerializer, SaleBuySerializer, SaleReceiveItemSerializer,
    PurchaseSerializer, PurchaseCreateSerializer, PurchaseSellSerializer, PurchaseReceiveGoldSerializer,
    ExchangeOptionSerializer, ExchangeSerializer
)


class AuctionViewSet(BaseGenericViewSet):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    serializer_action_classes = {
        'create': AuctionCreateSerializer,
        'bid': AuctionBidSerializer,
        'receive_item': AuctionReceiveItemSerializer,
        'receive_gold': AuctionReceiveGoldSerializer
    }

    def create(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['get'], detail=False)
    def active(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(due_time__gt=localtime())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def todo(self, request):
        chara = self.get_chara()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(
            Q(
                Q(bidder__isnull=True, item_received=False) | Q(bidder__isnull=False, gold_received=False),
                seller=chara
            ) |
            Q(bidder=chara, item_received=False),
            due_time__lt=localtime()
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def bid(self, request, pk):
        chara = self.get_chara()
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['post'], detail=True, url_path='receive-item')
    def receive_item(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['post'], detail=True, url_path='receive-gold')
    def receive_gold(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class SaleViewSet(BaseGenericViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    serializer_action_classes = {
        'create': SaleCreateSerializer,
        'buy': SaleBuySerializer,
        'receive_item': SaleReceiveItemSerializer
    }

    def create(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['get'], detail=False)
    def active(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(buyer__isnull=True, due_time__gt=localtime())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def todo(self, request):
        chara = self.get_chara()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(seller=chara, buyer__isnull=True, item_received=False, due_time__lt=localtime())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def buy(self, request, pk):
        chara = self.get_chara()
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['post'], detail=True, url_path='receive-item')
    def receive_item(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class PurchaseViewSet(BaseGenericViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    serializer_action_classes = {
        'create': PurchaseCreateSerializer,
        'sell': PurchaseSellSerializer,
        'receive_gold': PurchaseReceiveGoldSerializer
    }

    def create(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['get'], detail=False)
    def active(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(seller__isnull=True, due_time__gt=localtime())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def todo(self, request):
        chara = self.get_chara()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(buyer=chara, seller__isnull=True, gold_received=False, due_time__lt=localtime())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def sell(self, request, pk):
        chara = self.get_chara()
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['post'], detail=True, url_path='receive-gold')
    def receive_gold(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class ExchangeOptionViewSet(ListModelMixin, BaseGenericViewSet):
    queryset = ExchangeOption.objects.all()
    serializer_class = ExchangeOptionSerializer
    serializer_action_classes = {
        'exchange': ExchangeSerializer,
    }

    @action(methods=['post'], detail=True)
    def exchange(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})
