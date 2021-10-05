from django.db import models
from base.models import BaseModel


class Auction(BaseModel):
    seller = models.ForeignKey("chara.Chara", related_name="auction_seller_of", on_delete=models.PROTECT)

    item = models.ForeignKey("item.Item", null=True, on_delete=models.SET_NULL)
    reserve_price = models.BigIntegerField()

    bidder = models.ForeignKey("chara.Chara", null=True, related_name="auction_bidder_of", on_delete=models.PROTECT)
    bid_price = models.BigIntegerField(null=True)
    deposit = models.BigIntegerField(null=True, default=0)

    due_time = models.DateTimeField()

    item_received = models.BooleanField(default=False)
    gold_received = models.BooleanField(default=False)


class Sale(BaseModel):
    seller = models.ForeignKey("chara.Chara", related_name="sale_seller_of", on_delete=models.PROTECT)

    item = models.ForeignKey("item.Item", null=True, on_delete=models.SET_NULL)
    price = models.BigIntegerField()
    deposit = models.BigIntegerField(null=True, default=0)

    buyer = models.ForeignKey("chara.Chara", null=True, related_name="sale_buyer_of", on_delete=models.PROTECT)

    due_time = models.DateTimeField()

    item_received = models.BooleanField(default=False)


class Purchase(BaseModel):
    buyer = models.ForeignKey("chara.Chara", related_name="purchase_buyer_of", on_delete=models.PROTECT)

    item_type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT)
    number = models.IntegerField()
    price = models.BigIntegerField()

    seller = models.ForeignKey("chara.Chara", null=True, related_name="purchase_seller_of", on_delete=models.PROTECT)
    item = models.ForeignKey("item.Item", null=True, on_delete=models.SET_NULL)

    due_time = models.DateTimeField()

    gold_received = models.BooleanField(default=False)


class ExchangeOption(BaseModel):
    item_type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT)


class ExchangeOptionRequirement(BaseModel):
    exchange_option = models.ForeignKey("trade.ExchangeOption", related_name="requirements", on_delete=models.CASCADE)
    item_type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT)
    number = models.IntegerField()


class StoreOption(BaseModel):
    STORE_TYPE_CHOICES = [(x, x) for x in ['weapon', 'armor', 'jewelry', 'item']]

    item_type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT)
    price = models.IntegerField()

    store_type = models.CharField(choices=STORE_TYPE_CHOICES, max_length=10)
    location_element_type = models.ForeignKey("world.ElementType", null=True, on_delete=models.PROTECT)


class Lottery(BaseModel):
    name = models.CharField(max_length=100)
    nth = models.IntegerField()
    price = models.BigIntegerField()
    number_min = models.IntegerField()
    number_max = models.IntegerField()
    chara_ticket_limit = models.IntegerField()

    gold = models.BigIntegerField()


class LotteryTicket(BaseModel):
    lottery = models.ForeignKey("trade.Lottery", related_name='tickets', on_delete=models.CASCADE)
    nth = models.IntegerField()
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE)
    number = models.IntegerField()
