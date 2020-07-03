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

    def make(self, number):
        # equipment
        if self.category_id == 1:
            return [
                Equipment.objects.create(
                    type=self, number=1, element_type=self.element_type, custom_name=self.name,
                    attack=self.attack, defense=self.defense,
                    weight=self.weight, ability_1_id=self.ability_1_id, ability_2_id=self.ability_2_id
                ).item_ptr
                for i in range(number)
            ]

        # others
        else:
            return [Item(type=self, number=number)]


class Item(BaseModel):
    id = models.BigAutoField(primary_key=True)
    type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT)
    number = models.PositiveIntegerField()


class Equipment(Item):
    QUALITY_CHOICES = [(x, x) for x in ['稀有', '優良', '普通']]

    quality = models.CharField(max_length=2, choices=QUALITY_CHOICES)

    custom_name = models.CharField(max_length=20)

    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)

    attack = models.IntegerField(default=0)
    defense = models.IntegerField(default=0)
    weight = models.IntegerField(default=0)

    ability_1 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_1_items", on_delete=models.PROTECT)
    ability_2 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_2_items", on_delete=models.PROTECT)
