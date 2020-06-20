from django.db import models


class BaseManager(models.Manager):
    def lock_by_pks(self, pks):
        queryset = self.get_queryset().select_for_update().filter(pk__in=pks)
        obj_dict = {obj.pk: obj for obj in queryset}
        return [obj_dict.get(pk) for pk in pks]


class BaseModel(models.Model):
    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

    objects = BaseManager()

    class Meta:
        abstract = True

    def lock(self):
        return type(self).objects.select_for_update().get(pk=self.pk)


class BaseBuffType(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    is_positive = models.BooleanField()

    class Meta:
        abstract = True
