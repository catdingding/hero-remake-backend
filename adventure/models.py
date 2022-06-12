from django.db import models
from base.models import BaseModel, BaseSkillSetting


class Adventure(BaseModel):
    name = models.CharField(max_length=30)
    cost = models.IntegerField()
    max_step = models.IntegerField()


class AdventureStep(BaseModel):
    TYPE_CHOICES = [(x, x) for x in ['battle', 'event', 'scene']]

    adventure = models.ForeignKey("adventure.Adventure", related_name="steps", on_delete=models.CASCADE)
    step = models.IntegerField()

    name = models.CharField(max_length=30)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    battle = models.ForeignKey("adventure.AdventureBattle", null=True, on_delete=models.PROTECT)
    event = models.ForeignKey("adventure.AdventureEvent", null=True, on_delete=models.PROTECT)
    scene = models.ForeignKey("asset.Scene", null=True, on_delete=models.PROTECT)

    description = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('adventure', 'step')


class AdventureBattle(BaseModel):
    name = models.CharField(max_length=30, unique=True)
    monsters = models.ManyToManyField("battle.Monster")
    description = models.CharField(max_length=255, blank=True)


class AdventureEventEffectType(BaseModel):
    name = models.CharField(max_length=30, unique=True)


class AdventureEventEffect(BaseModel):
    type = models.ForeignKey("adventure.AdventureEventEffectType", on_delete=models.CASCADE)
    name = models.CharField(max_length=30, unique=True)
    param_1 = models.IntegerField(null=True)
    param_2 = models.IntegerField(null=True)


class AdventureEvent(BaseModel):
    CHOOSER_CHOICES = [(x, x) for x in ['random', 'chara']]

    chooser = models.CharField(max_length=10, choices=CHOOSER_CHOICES)
    candidate_effects = models.ManyToManyField("adventure.AdventureEventEffect")

    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=255, blank=True)


class AdventureRecord(BaseModel):
    STATUS_CHOICES = [(x, x) for x in ['inactive', 'active', 'ended']]

    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE)
    adventure = models.ForeignKey("adventure.Adventure", related_name="records", on_delete=models.CASCADE)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')
    current_step = models.PositiveIntegerField(default=0)

    difficulty = models.FloatField(default=1)
    abilities = models.ManyToManyField("ability.Ability")

    class Meta:
        unique_together = ('chara', 'adventure')
