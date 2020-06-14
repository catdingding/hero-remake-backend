from django.db import models
from base.models import BaseModel

from rest_framework.exceptions import APIException


class ItemEffect(BaseModel):
    name = models.CharField(max_length=10, unique=True)


class ItemCategory(BaseModel):
    name = models.CharField(max_length=10, unique=True)


class ItemType(BaseModel):
    name = models.CharField(max_length=30, unique=True)

    category = models.ForeignKey("item.ItemCategory", on_delete=models.PROTECT)
    element_type = models.ForeignKey("world.ElementType", null=True, on_delete=models.PROTECT)
    attribute_type = models.ForeignKey("world.AttributeType", null=True, on_delete=models.PROTECT)
    slot_type = models.ForeignKey("world.SlotType", null=True, on_delete=models.PROTECT)

    use_effect = models.ForeignKey("item.ItemEffect", null=True, on_delete=models.PROTECT)
    rank = models.IntegerField(null=True)
    # if True, disappear after use
    is_consumable = models.BooleanField()

    value = models.IntegerField(default=0)

    power = models.IntegerField(default=0)
    attack = models.IntegerField(default=0)
    defense = models.IntegerField(default=0)
    weight = models.IntegerField(default=0)

    ability_1 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_1_itemtypes", on_delete=models.PROTECT)
    ability_2 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_2_itemtypes", on_delete=models.PROTECT)

    description = models.CharField(max_length=100)


class Item(BaseModel):
    id = models.BigAutoField(primary_key=True)
    type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT)
    number = models.PositiveIntegerField()
    equipment_profile = models.OneToOneField("item.EquipmentProfile", null=True, on_delete=models.PROTECT)


class EquipmentProfile(BaseModel):
    QUALITY_CHOICES = [(x, x) for x in ['S', 'A', 'B']]

    quality = models.CharField(max_length=1, choices=QUALITY_CHOICES)

    custom_name = models.CharField(max_length=20)

    addition_attack = models.IntegerField(default=0)
    addition_weight = models.IntegerField(default=0)

    ability_1 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_1_items", on_delete=models.PROTECT)
    ability_2 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_2_items", on_delete=models.PROTECT)
