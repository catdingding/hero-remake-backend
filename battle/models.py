from django.db import models
from base.models import BaseModel


class BattleMap(BaseModel):
    name = models.CharField(max_length=20, unique=True)


class Monster(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)

    hp = models.PositiveIntegerField()
    mp = models.PositiveIntegerField()

    abilities = models.ManyToManyField("ability.Ability")


class MonsterAttribute(BaseModel):
    monster = models.ForeignKey("battle.Monster", on_delete=models.CASCADE, related_name="attributes")
    type = models.ForeignKey("world.AttributeType", on_delete=models.PROTECT)
    value = models.IntegerField()

    class Meta:
        unique_together = ('monster', 'type')


class MonsterSkillSetting(BaseModel):
    monster = models.ForeignKey("battle.Monster", on_delete=models.CASCADE, related_name="skill_settings")
    skill = models.ForeignKey("job.Skill", on_delete=models.CASCADE)

    hp_percentage = models.PositiveSmallIntegerField()
    mp_percentage = models.PositiveSmallIntegerField()

    priority = models.PositiveSmallIntegerField()


class BattleMapMonster(BaseModel):
    battle_map = models.ForeignKey("battle.BattleMap", on_delete=models.CASCADE)
    monster = models.ForeignKey("battle.Monster", on_delete=models.CASCADE, related_name="monsters")

    probability = models.PositiveIntegerField(default=10000)
