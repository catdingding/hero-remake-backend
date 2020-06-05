from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

    class Meta:
        abstract = True


class BaseBuffType(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    is_positive = models.BooleanField()

    class Meta:
        abstract = True
