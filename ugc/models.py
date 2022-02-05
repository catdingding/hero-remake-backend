from django.db import models
from base.models import BaseModel, BaseSkillSetting


class UGCMonster(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE)
    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=200, blank=True)
    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)

    hp = models.PositiveIntegerField()
    mp = models.PositiveIntegerField()

    abilities = models.ManyToManyField("ability.Ability")


class UGCMonsterAttribute(BaseModel):
    monster = models.ForeignKey("ugc.UGCMonster", on_delete=models.CASCADE, related_name="attributes")
    type = models.ForeignKey("world.AttributeType", on_delete=models.PROTECT)
    value = models.IntegerField()

    class Meta:
        unique_together = ('monster', 'type')


class UGCMonsterSkillSetting(BaseSkillSetting):
    monster = models.ForeignKey("ugc.UGCMonster", on_delete=models.CASCADE, related_name="skill_settings")


class UGCDungeon(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE)

    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=200, blank=True)

    max_floor = models.IntegerField()


class UGCDungeonFloor(BaseModel):
    dungeon = models.ForeignKey("ugc.UGCDungeon", related_name="floors", on_delete=models.CASCADE)
    floor = models.IntegerField()

    class Meta:
        unique_together = ('dungeon', 'floor')


class UGCDungeonFloorMonster(BaseModel):
    dungeon_floor = models.ForeignKey("ugc.UGCDungeonFloor", related_name="monsters", on_delete=models.CASCADE)
    monster = models.ForeignKey("ugc.UGCMonster", on_delete=models.PROTECT)


class CharaUGCDungeonRecord(BaseModel):
    STATUS_CHOICES = [(x, x) for x in ['inactive', 'active', 'ended']]

    chara = models.ForeignKey("chara.Chara", related_name="ugc_dungeon_records", on_delete=models.CASCADE)
    dungeon = models.ForeignKey("ugc.UGCDungeon", related_name='chara_records', on_delete=models.CASCADE)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')
    start_floor = models.PositiveIntegerField(default=0)
    current_floor = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('chara', 'dungeon')
