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


class BaseSkillSetting(BaseModel):
    skill = models.ForeignKey("job.Skill", on_delete=models.CASCADE)

    hp_percentage = models.PositiveSmallIntegerField()
    mp_percentage = models.PositiveSmallIntegerField()

    defender_hp_percentage = models.PositiveSmallIntegerField(default=100)
    defender_mp_percentage = models.PositiveSmallIntegerField(default=100)

    times_limit = models.PositiveIntegerField(default=0)
    probability = models.PositiveSmallIntegerField(default=100)

    order = models.IntegerField()

    class Meta:
        abstract = True
