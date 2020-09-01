from django.db import models
from base.models import BaseModel, BaseBuffType


class ElementType(BaseModel):
    en_name = models.CharField(max_length=10)
    name = models.CharField(max_length=10, unique=True)
    suppressed_by = models.ForeignKey("world.ElementType", null=True, on_delete=models.PROTECT)


class AttributeType(BaseModel):
    en_name = models.CharField(max_length=10)
    name = models.CharField(max_length=10, unique=True)
    class_name = models.CharField(max_length=10, unique=True)


class SlotType(BaseModel):
    en_name = models.CharField(max_length=10)
    name = models.CharField(max_length=10, unique=True)


class Location(BaseModel):
    x = models.IntegerField()
    y = models.IntegerField()
    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)
    battle_map = models.ForeignKey("battle.BattleMap", on_delete=models.PROTECT)
    chaos_score = models.PositiveIntegerField()

    class Meta:
        unique_together = ('x', 'y')


class LocationBuffType(BaseBuffType):
    pass


class LocationBuff(BaseModel):
    location = models.ForeignKey("world.Location", on_delete=models.CASCADE)
    type = models.ForeignKey("world.LocationBuffType", on_delete=models.CASCADE)
    value = models.IntegerField(null=True)
    due_date = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('location', 'type')
