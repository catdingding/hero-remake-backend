from django.db import models
from base.models import BaseModel


class Town(BaseModel):
    name = models.CharField(max_length=10, unique=True)
    location = models.OneToOneField("world.Location", unique=True, on_delete=models.PROTECT)

    description = models.CharField(max_length=200)


class BuildingType(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    max_level = models.IntegerField()


class TownBuilding(BaseModel):
    town = models.ForeignKey("town.Town", on_delete=models.CASCADE, related_name="buildings")
    type = models.ForeignKey("town.BuildingType", on_delete=models.PROTECT)
    level = models.IntegerField(default=1)

    class Meta:
        unique_together = ('town', 'type')
