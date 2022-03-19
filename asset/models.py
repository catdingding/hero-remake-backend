from django.db import models
from base.models import BaseModel


class Image(BaseModel):
    name = models.CharField(max_length=20)
    path = models.CharField(max_length=100)
