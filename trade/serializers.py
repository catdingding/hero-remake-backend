from datetime import timedelta

from django.utils.timezone import localtime
from django.db.models import F

from rest_framework import serializers

from base.serializers import (
    BaseSerializer, BaseModelSerializer, TransferPermissionCheckerMixin, SerpyModelSerializer,
    LockedEquipmentCheckMixin
)
from item.serializers import ItemTypeSerializer, ItemSerializer
from chara.serializers import CharaProfileSerializer
from chara.models import Chara
from trade.models import (
    Auction, Sale, Purchase, ExchangeOption, ExchangeOptionRequirement, StoreOption, Lottery, LotteryTicket,
    Parcel
)
from item.models import Item, ItemTypePoolGroup

from chara.achievement import update_achievement_counter
from system.utils import push_log, send_private_message_by_system


class AuctionSerializer(SerpyModelSerializer):
    item = ItemSerializer()
    seller = CharaProfileSerializer(fields=['id', 'name'])
    bidder = CharaProfileSerializer(fields=['id', 'name'])

    class Meta:
        model = Auction
        fields = ['id', 'seller', 'item', 'reserve_price', 'bidder', 'bid_price', 'due_time']


class AuctionCreateSerializer(LockedEquipmentCheckMixin, TransferPermissionCheckerMixin, BaseModelSerializer):
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

        deposit = max(100000, validated_data['reserve_price'] // 100)
        self.chara.lose_gold(deposit)
        self.chara.save()

        auction = Auction.objects.create(seller=self.chara, item=item, deposit=deposit,
                                         due_time=due_time, **validated_data)

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
        auction.due_time = max(auction.due_time, localtime() + timedelta(minutes=10))
        auction.save()

        push_log("拍賣", f"{self.chara.name}在拍賣場對{auction.item.type.name}*{auction.item.number}出價{auction.bid_price}")
        return auction

    def validate(self, data):
        if self.instance.bid_price is not None and data['bid_price'] < self.instance.bid_price * 1.1:
            raise serializers.ValidationError("出價必須高於當前最高出價*1.1")
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
        self.chara.gold += (auction.bid_price + auction.deposit)
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


class SaleSerializer(SerpyModelSerializer):
    item = ItemSerializer()
    seller = CharaProfileSerializer(fields=['id', 'name'])

    class Meta:
        model = Sale
        fields = ['id', 'seller', 'item', 'price', 'due_time']


class SaleCreateSerializer(LockedEquipmentCheckMixin, TransferPermissionCheckerMixin, BaseModelSerializer):
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

        deposit = max(100000, validated_data['price'] // 100)
        self.chara.lose_gold(deposit)
        self.chara.save()

        sale = Sale.objects.create(seller=self.chara, item=item, deposit=deposit, due_time=due_time, **validated_data)

        push_log("交易", f"{self.chara.name}在出售所上架了{item.type.name}*{item.number}，價格{sale.price}，時限{hours}小時")
        return sale


class SaleBuySerializer(BaseSerializer):
    def update(self, sale, validated_data):
        chara, seller = Chara.objects.lock_by_pks([self.chara.id, sale.seller.id])

        seller.gold += (sale.price + sale.deposit)
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


class PurchaseSerializer(SerpyModelSerializer):
    item_type = ItemTypeSerializer(fields=['name', 'description'])
    buyer = CharaProfileSerializer(fields=['id', 'name'])

    class Meta:
        model = Purchase
        fields = ['id', 'buyer', 'item_type', 'number', 'price', 'item', 'due_time']


class PurchaseCreateSerializer(BaseModelSerializer):
    number = serializers.IntegerField(min_value=1)
    price = serializers.IntegerField(min_value=1)
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
        push_log("收購", f"{self.chara.name}以{purchase.price}金錢的價格收購{purchase.item_type.name}*{purchase.number}")
        return purchase

    def validate_item_type(self, item_type):
        if item_type.category_id == 1:
            raise serializers.ValidationError("目前無法收購裝備")
        return item_type


class PurchaseSellSerializer(BaseSerializer):
    def update(self, purchase, validated_data):
        chara, buyer = Chara.objects.lock_by_pks([self.chara.id, purchase.buyer.id])

        chara.gold += purchase.price
        chara.save()

        item = chara.lose_items('bag', [Item(type_id=purchase.item_type_id, number=purchase.number)], mode='return')[0]
        item.save()

        purchase.seller = chara
        purchase.item = item
        purchase.save()

        push_log(
            "收購", f"{self.chara.name}向{purchase.buyer.name}提交{purchase.item_type.name}*{purchase.number}，獲得了{purchase.price}金錢")

        return purchase

    def validate(self, data):
        if self.instance.seller is not None:
            raise serializers.ValidationError("收購已完成")
        if self.chara == self.instance.buyer:
            raise serializers.ValidationError("不可提交物品給自己")
        if localtime() > self.instance.due_time:
            raise serializers.ValidationError("已超過收購時間")

        return data


class PurchaseReceiveSerializer(BaseSerializer):
    def update(self, purchase, validated_data):
        if purchase.seller is None and not purchase.gold_received:
            self.chara.gold += purchase.price
            self.chara.save()

            purchase.gold_received = True

        if purchase.seller and purchase.item:
            self.chara.get_items('bag', [purchase.item])
            purchase.item = None

        purchase.save()

        return purchase

    def validate(self, data):
        if self.instance.seller is not None and self.instance.item is None:
            raise serializers.ValidationError("已領取物品")
        if self.instance.seller is None:
            if self.instance.gold_received:
                raise serializers.ValidationError("已領取金錢")
            if localtime() <= self.instance.due_time:
                raise serializers.ValidationError("尚未結束收購")

        if self.chara != self.instance.buyer:
            raise serializers.ValidationError("僅收購者可領取金錢/物品")
        return data


class ExchangeOptionRequirementSerializer(SerpyModelSerializer):
    item_type = ItemTypeSerializer(fields=['name', 'description'])

    class Meta:
        model = ExchangeOptionRequirement
        fields = ['item_type', 'number']


class ExchangeOptionSerializer(SerpyModelSerializer):
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


class StoreOptionSerializer(SerpyModelSerializer):
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


class SellItemSerializer(LockedEquipmentCheckMixin, BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        item = self.validated_data['item']
        name = item.name
        number = self.validated_data['number']
        item.number = number
        items = [item]

        self.chara.lose_items('bag', items)
        gold = item.type.value * number // 2
        self.chara.gold += gold
        self.chara.save()

        return {'display_message': f'出售了{name}*{number}，獲得了{gold}金錢'}


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


class MemberShopBuyPetSerializer(BaseSerializer):
    number = serializers.IntegerField(min_value=1)

    def save(self):
        number = self.validated_data['number']

        items = []
        group = ItemTypePoolGroup.objects.get(id=13)
        for i in range(number):
            items.extend(group.pick())

        self.chara.get_items('bag', items)
        self.chara.lose_member_point(25 * number)
        self.chara.save()

        return {'display_message': f'獲得了{"、".join(x.name for x in items)}'}


class LotteryTicketSerializer(SerpyModelSerializer):
    class Meta:
        model = LotteryTicket
        fields = ['number']


class LotterySerializer(SerpyModelSerializer):
    tickets = LotteryTicketSerializer(many=True)

    class Meta:
        model = Lottery
        fields = ['id', 'name', 'nth', 'price', 'number_min', 'number_max', 'gold', 'chara_ticket_limit', 'tickets']


class BuyLotterySerializer(BaseSerializer):
    lottery = serializers.PrimaryKeyRelatedField(queryset=Lottery.objects.all())
    number = serializers.IntegerField()

    def save(self):
        lottery = self.validated_data['lottery']

        self.chara.lose_gold(lottery.price)
        self.chara.save()

        LotteryTicket.objects.create(
            lottery=lottery, nth=lottery.nth,
            chara=self.chara, number=self.validated_data['number']
        )
        Lottery.objects.filter(id=lottery.id).update(gold=F('gold') + int(lottery.price * 0.8))

        # 彩券購買次數
        update_achievement_counter(self.chara.id, 15, 1, 'increase')

    def validate(self, data):
        bought_ticket_count = LotteryTicket.objects.filter(
            lottery=data['lottery'], nth=data['lottery'].nth, chara=self.chara
        ).count()
        if bought_ticket_count >= data['lottery'].chara_ticket_limit:
            raise serializers.ValidationError("超過本期購買數量限制")
        if not data['lottery'].number_max >= data['number'] >= data['lottery'].number_min:
            raise serializers.ValidationError("號碼超出範圍")
        return data


class ParcelSerializer(SerpyModelSerializer):
    sender = CharaProfileSerializer(fields=['id', 'name'])
    receiver = CharaProfileSerializer(fields=['id', 'name'])
    item = ItemSerializer()

    class Meta:
        model = Parcel
        fields = ['id', 'sender', 'receiver', 'item', 'price', 'message']


class ParcelCreateSerializer(BaseModelSerializer):
    number = serializers.IntegerField(min_value=1)

    class Meta:
        model = Parcel
        fields = ['receiver', 'item', 'number', 'price', 'message']

    def create(self, validated_data):
        item = validated_data.pop('item')
        item.number = validated_data.pop('number')

        item = self.chara.lose_items('bag', [item], mode='return')[0]
        item.save()

        parcel = Parcel.objects.create(sender=self.chara, item=item, **validated_data)

        message = (
            f"{self.chara.name}向{validated_data['receiver'].name}寄送了包含{item.type.name}*{item.number}的包裹"
            f"，應付金額為{validated_data['price']}"
        )
        push_log("包裹", message)
        send_private_message_by_system(self.chara.id, validated_data['receiver'].id, message)

        return parcel

    def validate(self, data):
        if Parcel.objects.filter(sender=self.chara).count() >= 10:
            raise serializers.ValidationError("建立的待領取包裹需<=10")
        return data


class ParcelReceiveSerializer(BaseSerializer):
    def save(self):
        item = self.instance.item
        chara, sender = Chara.objects.lock_by_pks([self.chara.id, getattr(self.instance.sender, 'id', None)])
        message = f"支付{self.instance.price}金錢，領取了{item.name}*{item.number}"

        chara.lose_gold(self.instance.price)
        chara.save()

        chara.get_items('bag', [item])

        if sender is not None:
            sender.gold += self.instance.price
            sender.save()
            send_private_message_by_system(chara.id, sender.id, message)

        self.instance.delete()

        return {'display_message': message}


class ParcelCancelSerializer(BaseSerializer):
    def save(self):
        item = self.instance.item
        receiver = self.instance.receiver
        message = f"收回了{item.name}*{item.number}的包裹"

        self.chara.get_items('bag', [item])

        self.instance.delete()

        send_private_message_by_system(self.chara.id, receiver.id, message)

        return {'display_message': message}
