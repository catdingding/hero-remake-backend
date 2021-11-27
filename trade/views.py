from django.db.models import Q, Prefetch, OuterRef, Subquery
from django.utils.timezone import localtime
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin

from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaPostViewMixin
from base.pagination import BasePagination
from item.filters import ItemFilter

from trade.models import Auction, Sale, Purchase, ExchangeOption, StoreOption, Lottery, LotteryTicket, Parcel
from trade.serializers import (
    AuctionSerializer, AuctionCreateSerializer, AuctionBidSerializer,
    AuctionReceiveItemSerializer, AuctionReceiveGoldSerializer,
    SaleSerializer, SaleCreateSerializer, SaleBuySerializer, SaleReceiveItemSerializer,
    PurchaseSerializer, PurchaseCreateSerializer, PurchaseSellSerializer, PurchaseReceiveSerializer,
    ExchangeOptionSerializer, ExchangeSerializer,
    StoreOptionSerializer, StoreBuySerializer, SellItemSerializer,
    MemberShopBuyColdDownBonusSerializer, MemberShopBuyAutoHealSerializer, MemberShopBuyQuestBonusSerializer,
    MemberShopBuyBagItemLimitSerializer, MemberShopBuyLevelDownSerializer, MemberShopBuyPetSerializer,
    BuyLotterySerializer, LotterySerializer,
    ParcelSerializer, ParcelCreateSerializer, ParcelCancelSerializer, ParcelReceiveSerializer
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
    check_in_town = True

    def create(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['get'], detail=False, pagination_class=BasePagination, filterset_class=ItemFilter.set_item_field('item'))
    def active(self, request):
        queryset = self.get_queryset().filter(due_time__gt=localtime())
        return self.list(request, queryset)

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
    check_in_town = True

    def create(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['get'], detail=False, pagination_class=BasePagination, filterset_class=ItemFilter.set_item_field('item'))
    def active(self, request):
        queryset = self.get_queryset().filter(buyer__isnull=True, due_time__gt=localtime())
        return self.list(request, queryset)

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
        'receive': PurchaseReceiveSerializer
    }
    check_in_town = True

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
        queryset = queryset.filter(
            Q(seller__isnull=False, item__isnull=False) |
            Q(seller__isnull=True, gold_received=False, due_time__lt=localtime()),
            buyer=chara
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def sell(self, request, pk):
        chara = self.get_chara()
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['post'], detail=True, url_path='receive')
    def receive(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class ExchangeOptionViewSet(ListModelMixin, BaseGenericViewSet):
    queryset = ExchangeOption.objects.select_related('item_type').prefetch_related('requirements__item_type').all()
    serializer_class = ExchangeOptionSerializer
    serializer_action_classes = {
        'exchange': ExchangeSerializer,
    }
    check_in_town = True

    @action(methods=['post'], detail=True)
    def exchange(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)


class StoreOptionViewSet(ListModelMixin, BaseGenericViewSet):
    queryset = StoreOption.objects.select_related(
        'item_type__slot_type', 'item_type__ability_1', 'item_type__ability_2'
    ).all()
    serializer_class = StoreOptionSerializer
    serializer_action_classes = {
        'buy': StoreBuySerializer,
    }
    filterset_fields = ['store_type']
    check_in_town = True

    def get_queryset(self):
        queryset = super().get_queryset()
        location = self.get_chara().location
        if not hasattr(location, 'town'):
            return queryset.filter(pk__isnull=True)
        else:
            return queryset.filter(
                Q(location_element_type=location.element_type) | Q(location_element_type__isnull=True)
            )

    @action(methods=['post'], detail=True)
    def buy(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)


class SellItemView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SellItemSerializer
    check_in_town = True


class MemberShopViewSet(BaseGenericViewSet):
    serializer_action_classes = {
        'buy_cold_down_bonus': MemberShopBuyColdDownBonusSerializer,
        'buy_quest_bonus': MemberShopBuyQuestBonusSerializer,
        'buy_auto_heal': MemberShopBuyAutoHealSerializer,
        'buy_bag_item_limit': MemberShopBuyBagItemLimitSerializer,
        'buy_level_down': MemberShopBuyLevelDownSerializer,
        'buy_pet': MemberShopBuyPetSerializer
    }

    def buy(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result)

    @action(methods=['post'], detail=False, url_path='buy-cold-down-bonus')
    def buy_cold_down_bonus(self, request):
        return self.buy(request)

    @action(methods=['post'], detail=False, url_path='buy-quest-bonus')
    def buy_quest_bonus(self, request):
        return self.buy(request)

    @action(methods=['post'], detail=False, url_path='buy-auto-heal')
    def buy_auto_heal(self, request):
        return self.buy(request)

    @action(methods=['post'], detail=False, url_path='buy-bag-item-limit')
    def buy_bag_item_limit(self, request):
        return self.buy(request)

    @action(methods=['post'], detail=False, url_path='buy-level-down')
    def buy_level_down(self, request):
        return self.buy(request)

    @action(methods=['post'], detail=False, url_path='buy-pet')
    def buy_pet(self, request):
        return self.buy(request)


class BuyLotteryView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = BuyLotterySerializer
    check_in_town = True


class LotteryView(ListModelMixin, BaseGenericAPIView):
    queryset = Lottery.objects.all()
    serializer_class = LotterySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.prefetch_related(Prefetch(
            'tickets',
            LotteryTicket.objects.filter(
                nth=Subquery(Lottery.objects.filter(id=OuterRef('lottery')).values('nth')),
                chara=self.get_chara()
            )
        ))

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ParcelViewSet(BaseGenericViewSet):
    queryset = Parcel.objects.all()
    serializer_class = ParcelSerializer
    serializer_action_classes = {
        'create': ParcelCreateSerializer,
        'cancel': ParcelCancelSerializer,
        'receive': ParcelReceiveSerializer,
    }

    def create(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['get'], detail=False)
    def todo(self, request):
        chara = self.get_chara()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(Q(sender=chara) | Q(receiver=chara))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def cancel(self, request, pk):
        chara = self.get_chara()
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})

    @action(methods=['post'], detail=True)
    def receive(self, request, pk):
        chara = self.get_chara()
        serializer = self.get_serializer(self.get_object(lock=True), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})
