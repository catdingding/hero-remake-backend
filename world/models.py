from django.db import models
from base.models import BaseModel


class ElementType(BaseModel):
    en_name = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=10, unique=True)
    suppressed_by = models.ForeignKey("world.ElementType", null=True, on_delete=models.PROTECT)


class AttributeType(BaseModel):
    en_name = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=10, unique=True)
    class_name = models.CharField(max_length=10, unique=True)


class SlotType(BaseModel):
    en_name = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=10, unique=True)


class Location(BaseModel):
    x = models.IntegerField()
    y = models.IntegerField()
    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)
    battle_map = models.ForeignKey("battle.BattleMap", on_delete=models.PROTECT)
    country = models.ForeignKey("country.Country", related_name='locations', null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('x', 'y')


class LocationBuffEffect(BaseModel):
    name = models.CharField(max_length=20)


class LocationBuffType(BaseModel):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=100)

    effect = models.ForeignKey("world.LocationBuffEffect", on_delete=models.CASCADE)
    power = models.IntegerField()


class LocationBuff(BaseModel):
    location = models.ForeignKey("world.Location", related_name="buffs", on_delete=models.CASCADE)
    type = models.ForeignKey("world.LocationBuffType", on_delete=models.CASCADE)
    due_date = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('location', 'type')
