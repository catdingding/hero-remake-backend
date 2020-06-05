from django.db import models
from base.models import BaseModel


class AbilityType(BaseModel):
    name = models.CharField(max_length=20, unique=True)


class Ability(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    attribute_type = models.ForeignKey("world.AttributeType", null=True, on_delete=models.PROTECT)
    type = models.ForeignKey("AbilityType", on_delete=models.PROTECT)
    rank = models.IntegerField(null=True)

    power = models.FloatField()
    require_proficiency = models.PositiveIntegerField()

    description = models.CharField(max_length=100)
