from django.db import models
from base.models import BaseModel

class Log(BaseModel):
    type = models.CharField(max_length=20)
    message = models.CharField(max_length=200)

class WorldChat(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.SET_NULL)
    message = models.CharField(max_length=200)

class CountryChat(BaseModel):
    country = models.ForeignKey("country.Country", on_delete=models.SET_NULL)
    chara = models.ForeignKey("chara.Chara", on_delete=models.SET_NULL)
    message = models.CharField(max_length=200)

class PrivateChat(BaseModel):
    sender = models.ForeignKey("chara.Chara", on_delete=models.SET_NULL)
    receiver = models.ForeignKey("chara.Chara", on_delete=models.SET_NULL)
    message = models.CharField(max_length=200)
