from django.db import models
from base.models import BaseModel


class Country(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    king = models.ForeignKey("chara.Chara", null=True, on_delete=models.SET_NULL)

    gold = models.PositiveIntegerField()
