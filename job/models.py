from django.db import models
from base.models import BaseModel


class Job(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    attribute_type = models.ForeignKey("world.AttributeType", on_delete=models.PROTECT)
    rank = models.PositiveSmallIntegerField()

    base_hp = models.IntegerField(default=0)
    base_mp = models.IntegerField(default=0)

    description = models.CharField(max_length=100)


class JobAttribute(BaseModel):
    job = models.ForeignKey('job.Job', related_name='attributes', on_delete=models.CASCADE)
    type = models.ForeignKey("world.AttributeType", on_delete=models.PROTECT)

    base_value = models.IntegerField(default=0)
    require_value = models.IntegerField(default=0)
    require_proficiency = models.IntegerField(default=0)

    class Meta:
        unique_together = ('job', 'type')


class SkillType(BaseModel):
    name = models.CharField(max_length=20, unique=True)


class Skill(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    attribute_type = models.ForeignKey("world.AttributeType", null=True, on_delete=models.PROTECT)
    rank = models.IntegerField(null=True)
    type = models.ForeignKey("SkillType", on_delete=models.PROTECT)

    power = models.IntegerField()
    rate = models.IntegerField()
    mp_cost = models.IntegerField()
