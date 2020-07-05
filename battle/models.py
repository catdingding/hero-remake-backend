from django.db import models
from base.models import BaseModel


class BattleMap(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    proficiency = models.IntegerField()
    need_ticket = models.BooleanField()


class Monster(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)

    hp = models.PositiveIntegerField()
    mp = models.PositiveIntegerField()

    abilities = models.ManyToManyField("ability.Ability")

    gold = models.IntegerField()
    exp = models.IntegerField()


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

    order = models.IntegerField()


class BattleMapMonster(BaseModel):
    battle_map = models.ForeignKey("battle.BattleMap", related_name="monsters", on_delete=models.CASCADE)
    monster = models.ForeignKey("battle.Monster", on_delete=models.CASCADE)

    weight = models.PositiveIntegerField(default=10000)
