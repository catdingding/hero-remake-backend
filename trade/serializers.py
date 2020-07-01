from datetime import timedelta

from django.utils.timezone import localtime

from rest_framework import serializers

from base.serializers import BaseSerializer, BaseModelSerializer
from chara.models import Chara
from trade.models import Auction, Sale, Purchase, ExchangeOption, ExchangeOptionRequirement, StoreOption
from item.models import Item


class AuctionSerializer(BaseModelSerializer):
    class Meta:
        model = Auction
        fields = ['id', 'seller', 'item', 'reserve_price', 'bidder', 'bid_price', 'due_time']


class AuctionCreateSerializer(BaseModelSerializer):
    number = serializers.IntegerField(min_value=1)
    hours = serializers.IntegerField(min_value=1, max_value=24)

    class Meta:
        model = Auction
        fields = ['item', 'number', 'reserve_price', 'hours']
        extra_kwargs = {'item': {'allow_null': False}}

    def create(self, validated_data):
        hours = validated_data.pop('hours')
        due_time = localtime() + timedelta(hours=hours)

        item = validated_data.pop('item')
        item.number = validated_data.pop('number')

        item = self.chara.lose_items('bag', [item], mode='return')[0]
        item.save()
        auction = Auction.objects.create(seller=self.chara, item=item, due_time=due_time, **validated_data)

        return auction


class AuctionBidSerializer(BaseSerializer):
    bid_price = serializers.IntegerField(min_value=1)

    def update(self, auction, validated_data):
        chara, latest_bidder = Chara.objects.lock_by_pks([self.chara.id, auction.bidder])
        if latest_bidder:
            latest_bidder.gold += auction.bid_price
            latest_bidder.save()

        chara.lose_gold(validated_data['bid_price'])
        chara.save()

        auction.bidder = chara
        auction.bid_price = validated_data['bid_price']
        auction.save()

        return auction

    def validate(self, data):
        if self.instance.bid_price is not None and data['bid_price'] <= self.instance.bid_price:
            raise serializers.ValidationError("出價必須高於當前最高出價")
        if data['bid_price'] < self.instance.reserve_price:
            raise serializers.ValidationError("出價不得低於底價")
        if self.chara == self.instance.seller:
            raise serializers.ValidationError("不可向自己的商品投標")
        if self.chara == self.instance.bidder:
            raise serializers.ValidationError("你已是當前最高出價者")
        if localtime() > self.instance.due_time:
            raise serializers.ValidationError("已超過投標時間")

        return data


class AuctionReceiveGoldSerializer(BaseSerializer):
    def update(self, auction, validated_data):
        self.chara.gold += auction.bid_price
        self.chara.save()

        auction.gold_received = True
        auction.save()

        return auction

    def validate(self, data):
        if self.instance.gold_received:
            raise serializers.ValidationError("貨款已領取")
        if localtime() <= self.instance.due_time:
            raise serializers.ValidationError("尚未結標")
        if self.chara != self.instance.seller:
            raise serializers.ValidationError("僅出售者可領取貨款")
        if self.instance.bidder is None:
            raise serializers.ValidationError("流標商品無法領取貨款")
        return data


class AuctionReceiveItemSerializer(BaseSerializer):
    def update(self, auction, validated_data):
        self.chara.get_items('bag', [auction.item])

        auction.item = None
        auction.item_received = True
        auction.save()

        return auction

    def validate(self, data):
        if self.instance.item_received:
            raise serializers.ValidationError("物品已領取")
        if localtime() <= self.instance.due_time:
            raise serializers.ValidationError("尚未結標")
        if self.instance.bidder is None:
            if self.chara != self.instance.seller:
                raise serializers.ValidationError("僅出售者可領取流標商品")
        else:
            if self.chara != self.instance.bidder:
                raise serializers.ValidationError("僅得標者可領取得標商品")
        return data


class SaleSerializer(BaseModelSerializer):
    class Meta:
        model = Sale
        fields = ['id', 'seller', 'item', 'price', 'due_time']


class SaleCreateSerializer(BaseModelSerializer):
    number = serializers.IntegerField(min_value=1)
    hours = serializers.IntegerField(min_value=1, max_value=24)

    class Meta:
        model = Sale
        fields = ['item', 'price', 'number', 'hours']
        extra_kwargs = {'item': {'allow_null': False}}

    def create(self, validated_data):
        hours = validated_data.pop('hours')
        due_time = localtime() + timedelta(hours=hours)

        item = validated_data.pop('item')
        item.number = validated_data.pop('number')

        item = self.chara.lose_items('bag', [item], mode='return')[0]
        item.save()
        sale = Sale.objects.create(seller=self.chara, item=item, due_time=due_time, **validated_data)

        return sale


class SaleBuySerializer(BaseSerializer):
    def update(self, sale, validated_data):
        chara, seller = Chara.objects.lock_by_pks([self.chara.id, sale.seller.id])

        seller.gold += sale.price
        seller.save()

        chara.lose_gold(sale.price)
        chara.save()

        chara.get_items('bag', [sale.item])

        sale.buyer = chara
        sale.item = None
        sale.item_received = True
        sale.save()

        return sale

    def validate(self, data):
        if self.instance.buyer is not None:
            raise serializers.ValidationError("商品已被購買")
        if self.chara == self.instance.seller:
            raise serializers.ValidationError("不可購買自己的商品")
        if localtime() > self.instance.due_time:
            raise serializers.ValidationError("已超過購買時間")

        return data


class SaleReceiveItemSerializer(BaseSerializer):
    def update(self, sale, validated_data):
        self.chara.get_items('bag', [sale.item])

        sale.item = None
        sale.item_received = True
        sale.save()

        return sale

    def validate(self, data):
        if self.instance.buyer is not None:
            raise serializers.ValidationError("商品已售出")
        if self.instance.item_received:
            raise serializers.ValidationError("物品已領取")
        if localtime() <= self.instance.due_time:
            raise serializers.ValidationError("尚未結束販售")
        if self.chara != self.instance.seller:
            raise serializers.ValidationError("僅出售者可領取未售出商品")
        return data


class PurchaseSerializer(BaseModelSerializer):
    class Meta:
        model = Purchase
        fields = ['id', 'buyer', 'item_type', 'number', 'price', 'due_time']


class PurchaseCreateSerializer(BaseModelSerializer):
    hours = serializers.IntegerField(min_value=1, max_value=24)

    class Meta:
        model = Purchase
        fields = ['item_type', 'number', 'price', 'hours']

    def create(self, validated_data):
        hours = validated_data.pop('hours')
        due_time = localtime() + timedelta(hours=hours)

        self.chara.lose_gold(validated_data['price'])
        self.chara.save()

        purchase = Purchase.objects.create(buyer=self.chara, due_time=due_time, **validated_data)

        return purchase


class PurchaseSellSerializer(BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())

    def update(self, purchase, validated_data):
        chara, buyer = Chara.objects.lock_by_pks([self.chara.id, purchase.buyer.id])

        chara.gold += purchase.price
        chara.save()

        item = validated_data['item']
        item.number = purchase.number

        item = chara.lose_items('bag', [item], mode='return')[0]
        buyer.get_items('bag', [item])

        purchase.seller = chara
        purchase.gold_received = True
        purchase.save()

        return purchase

    def validate(self, data):
        if data['item'].type != self.instance.item_type:
            raise serializers.ValidationError("物品類型不符合收購條件")
        if self.instance.seller is not None:
            raise serializers.ValidationError("收購已完成")
        if self.chara == self.instance.buyer:
            raise serializers.ValidationError("不可販售物品給自己")
        if localtime() > self.instance.due_time:
            raise serializers.ValidationError("已超過收購時間")

        return data


class PurchaseReceiveGoldSerializer(BaseSerializer):
    def update(self, purchase, validated_data):
        self.chara.gold += purchase.price
        self.chara.save()

        purchase.gold_received = True
        purchase.save()

        return purchase

    def validate(self, data):
        if self.instance.seller is not None:
            raise serializers.ValidationError("收購已完成")
        if self.instance.gold_received:
            raise serializers.ValidationError("金錢已領取")
        if localtime() <= self.instance.due_time:
            raise serializers.ValidationError("尚未結束收購")
        if self.chara != self.instance.buyer:
            raise serializers.ValidationError("僅收購者可領取金錢")
        return data


class ExchangeOptionRequirementSerializer(BaseModelSerializer):
    class Meta:
        model = ExchangeOptionRequirement
        fields = ['item_type', 'number']


class ExchangeOptionSerializer(BaseModelSerializer):
    requirements = ExchangeOptionRequirementSerializer(many=True)

    class Meta:
        model = ExchangeOption
        fields = ['item_type', 'requirements']


class ExchangeSerializer(BaseSerializer):
    number = serializers.IntegerField(min_value=1)

    def save(self):
        number = self.validated_data['number']

        items_to_lose = [Item(type=r.item_type, number=r.number * number) for r in self.instance.requirements.all()]
        self.chara.lose_items('bag', items_to_lose)

        self.chara.get_items('bag', [Item(type=self.instance.item_type, number=number)])


class StoreOptionSerializer(BaseModelSerializer):
    class Meta:
        model = StoreOption
        fields = ['id', 'item_type', 'price']


class StoreBuySerializer(BaseSerializer):
    number = serializers.IntegerField(min_value=1)

    def save(self):
        number = self.validated_data['number']

        self.chara.lose_gold(self.instance.price * number)
        self.chara.get_items('bag', self.instance.item_type.make(number))
