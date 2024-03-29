from django.db import models
from base.models import BaseModel


class AbilityType(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    is_live = models.BooleanField()
    need_equip = models.BooleanField()


class Ability(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    attribute_type = models.ForeignKey("world.AttributeType", null=True, on_delete=models.PROTECT)
    type = models.ForeignKey("AbilityType", on_delete=models.PROTECT)
    rank = models.IntegerField(null=True)

    power = models.FloatField()
    require_proficiency = models.PositiveIntegerField()
    prerequisite = models.ForeignKey("ability.Ability", null=True, on_delete=models.PROTECT)

    description = models.CharField(max_length=100)


class AlchemyOption(BaseModel):
    require_power = models.IntegerField()

    item_type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT)
    proficiency_cost = models.IntegerField()
