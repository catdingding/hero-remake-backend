from datetime import timedelta

from django.utils.timezone import localtime

from rest_framework import serializers

from base.serializers import BaseSerializer, BaseModelSerializer
from item.serializers import ItemTypeSerializer, ItemSerializer
from chara.serializers import CharaProfileSerializer
from chara.models import Chara
from trade.models import Auction, Sale, Purchase, ExchangeOption, ExchangeOptionRequirement, StoreOption
from item.models import Item

from system.utils import push_log


class AuctionSerializer(BaseModelSerializer):
    item = ItemSerializer()
    seller = CharaProfileSerializer(fields=['id', 'name'])
    bidder = CharaProfileSerializer(fields=['id', 'name'])

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

        push_log("拍賣", f"{self.chara.name}在拍賣場上架了{item.type.name}*{item.number}，底價{auction.reserve_price}，時限{hours}小時")
        return auction


class AuctionBidSerializer(BaseSerializer):
    bid_price = serializers.IntegerField(min_value=1)

    def update(self, auction, validated_data):
        chara, latest_bidder = Chara.objects.lock_by_pks([self.chara.id, auction.bidder_id])
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
        item = auction.item
        self.chara.get_items('bag', [item])

        auction.item = None
        auction.item_received = True
        auction.save()

        if self.chara == auction.bidder:
            push_log("拍賣", f"{self.chara.name}以{auction.bid_price}金錢拍得了{item.type.name}*{item.number}")
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
    item = ItemSerializer()
    seller = CharaProfileSerializer(fields=['id', 'name'])

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

        push_log("交易", f"{self.chara.name}在出售所上架了{item.type.name}*{item.number}，價格{sale.price}，時限{hours}小時")
        return sale


class SaleBuySerializer(BaseSerializer):
    def update(self, sale, validated_data):
        chara, seller = Chara.objects.lock_by_pks([self.chara.id, sale.seller.id])

        seller.gold += sale.price
        seller.save()

        chara.lose_gold(sale.price)
        chara.save()

        item = sale.item
        chara.get_items('bag', [item])

        sale.buyer = chara
        sale.item = None
        sale.item_received = True
        sale.save()

        push_log("交易", f"{self.chara.name}以{sale.price}金錢買下了{item.type.name}*{item.number}")
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
    item_type = ItemTypeSerializer(fields=['name'])

    class Meta:
        model = ExchangeOptionRequirement
        fields = ['item_type', 'number']


class ExchangeOptionSerializer(BaseModelSerializer):
    item_type = ItemTypeSerializer()
    requirements = ExchangeOptionRequirementSerializer(many=True)

    class Meta:
        model = ExchangeOption
        fields = ['id', 'item_type', 'requirements']


class ExchangeSerializer(BaseSerializer):
    number = serializers.IntegerField(min_value=1)

    def save(self):
        number = self.validated_data['number']

        items_to_lose = [Item(type=r.item_type, number=r.number * number) for r in self.instance.requirements.all()]
        self.chara.lose_items('bag', items_to_lose)

        self.chara.get_items('bag', self.instance.item_type.make(number))

        return {'display_message': f'換取了{number}個{self.instance.item_type.name}'}


class StoreOptionSerializer(BaseModelSerializer):
    item_type = ItemTypeSerializer()

    class Meta:
        model = StoreOption
        fields = ['id', 'item_type', 'price']


class StoreBuySerializer(BaseSerializer):
    number = serializers.IntegerField(min_value=1)

    def save(self):
        number = self.validated_data['number']

        cost = self.instance.price * number
        self.chara.lose_gold(cost)
        self.chara.get_items('bag', self.instance.item_type.make(number))
        self.chara.save()

        return {'display_message': f'購買了{number}個{self.instance.item_type.name}'}


class SellItemSerializer(BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        item = self.validated_data['item']
        number = self.validated_data['number']
        item.number = number
        items = [item]

        self.chara.lose_items('bag', items)
        gold = item.type.value * number // 2
        self.chara.gold += gold
        self.chara.save()

        return {'display_message': f'出售物品，獲得了{gold}金錢'}


class MemberShopBuyColdDownBonusSerializer(BaseSerializer):
    def save(self):
        self.chara.lose_member_point(300)
        self.chara.has_cold_down_bonus = True
        self.chara.save()

        return {'display_message': '已成功購買冷卻加成'}

    def validate(self, data):
        if self.chara.has_cold_down_bonus:
            raise serializers.ValidationError("已購買冷卻加成")
        return data


class MemberShopBuyQuestBonusSerializer(BaseSerializer):
    def save(self):
        self.chara.lose_member_point(200)
        self.chara.has_quest_bonus = True
        self.chara.save()

        return {'display_message': '已成功購買任務加成'}

    def validate(self, data):
        if self.chara.has_quest_bonus:
            raise serializers.ValidationError("已購買任務加成")
        return data


class MemberShopBuyAutoHealSerializer(BaseSerializer):
    def save(self):
        self.chara.lose_member_point(200)
        self.chara.has_auto_heal = True
        self.chara.save()

        return {'display_message': '已成功購買自動回血回魔'}

    def validate(self, data):
        if self.chara.has_auto_heal:
            raise serializers.ValidationError("已購買自動回血回魔")
        return data


class MemberShopBuyBagItemLimitSerializer(BaseSerializer):
    number = serializers.IntegerField(min_value=1)

    def save(self):
        number = self.validated_data['number']

        self.chara.lose_member_point(20 * number)
        self.chara.bag_item_limit += number
        self.chara.save()

        return {'display_message': f'已成功擴充背包至{self.chara.bag_item_limit}格'}

    def validate(self, data):
        if self.chara.bag_item_limit + data['number'] > 60:
            raise serializers.ValidationError("背包最多擴充可至60格")
        return data


class MemberShopBuyLevelDownSerializer(BaseSerializer):
    number = serializers.IntegerField(min_value=1)

    def save(self):
        number = self.validated_data['number']

        self.chara.lose_member_point(20 * number)
        self.chara.exp -= 100 * number
        self.chara.save()

        self.chara.record.level_down_count += number
        self.chara.record.save()

        return {'display_message': f'已降低了{number}級'}

    def validate(self, data):
        if self.chara.record.level_down_count + data['number'] > 300:
            raise serializers.ValidationError("每次轉職最多可降低300等")
        if data['number'] * 100 > self.chara.exp:
            raise serializers.ValidationError("最多僅可降低至1級")
        return data
