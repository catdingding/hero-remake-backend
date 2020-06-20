from django.db import models
from base.models import BaseModel


class Auction(BaseModel):
    seller = models.ForeignKey("chara.Chara", related_name="auction_seller_of", on_delete=models.PROTECT)

    item = models.ForeignKey("item.Item", null=True, on_delete=models.PROTECT)
    reserve_price = models.BigIntegerField()

    bidder = models.ForeignKey("chara.Chara", null=True, related_name="auction_bidder_of", on_delete=models.PROTECT)
    bid_price = models.BigIntegerField(null=True)

    due_time = models.DateTimeField()

    item_received = models.BooleanField(default=False)
    gold_received = models.BooleanField(default=False)


class Sale(BaseModel):
    seller = models.ForeignKey("chara.Chara", related_name="sale_seller_of", on_delete=models.PROTECT)

    item = models.ForeignKey("item.Item", null=True, on_delete=models.PROTECT)
    price = models.BigIntegerField()

    buyer = models.ForeignKey("chara.Chara", null=True, related_name="sale_buyer_of", on_delete=models.PROTECT)

    due_time = models.DateTimeField()

    item_received = models.BooleanField(default=False)


class Purchase(BaseModel):
    buyer = models.ForeignKey("chara.Chara", related_name="purchase_buyer_of", on_delete=models.PROTECT)

    item_type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT)
    number = models.IntegerField()
    price = models.BigIntegerField()

    seller = models.ForeignKey("chara.Chara", null=True, related_name="purchase_seller_of", on_delete=models.PROTECT)

    due_time = models.DateTimeField()

    gold_received = models.BooleanField(default=False)
