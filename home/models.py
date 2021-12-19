from django.db import models
from base.models import BaseModel


class FarmingReward(BaseModel):
    item_type = models.ForeignKey("item.ItemType", related_name="farming_input_of", on_delete=models.PROTECT)

    reward_item_type = models.ForeignKey(
        "item.ItemType", related_name="farming_reward_of", null=True, on_delete=models.PROTECT)
    number = models.IntegerField(default=1)
