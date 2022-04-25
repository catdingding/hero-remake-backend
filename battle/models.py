from django.db import models
from base.models import BaseModel, BaseSkillSetting


class BattleEffectType(BaseModel):
    name = models.CharField(max_length=20, unique=True)


class BattleEffect(BaseModel):
    type = models.ForeignKey("battle.BattleEffectType", on_delete=models.PROTECT)
    name = models.CharField(max_length=20, unique=True)
    value = models.FloatField()
    description = models.CharField(max_length=100)


class BattleMap(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    exp = models.IntegerField()
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
    proficiency = models.IntegerField()


class MonsterAttribute(BaseModel):
    monster = models.ForeignKey("battle.Monster", on_delete=models.CASCADE, related_name="attributes")
    type = models.ForeignKey("world.AttributeType", on_delete=models.PROTECT)
    value = models.IntegerField()

    class Meta:
        unique_together = ('monster', 'type')


class MonsterSkillSetting(BaseSkillSetting):
    monster = models.ForeignKey("battle.Monster", on_delete=models.CASCADE, related_name="skill_settings")


class BattleMapMonster(BaseModel):
    battle_map = models.ForeignKey("battle.BattleMap", related_name="monsters", on_delete=models.CASCADE)
    monster = models.ForeignKey("battle.Monster", on_delete=models.CASCADE)

    weight = models.PositiveIntegerField(default=10000)


class Dungeon(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    max_floor = models.IntegerField()
    is_infinite = models.BooleanField(default=False)

    ticket_type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT, null=True)
    ticket_cost = models.IntegerField(default=0)

    gold_reward_per_floor = models.IntegerField(default=0)


class DungeonFloor(BaseModel):
    dungeon = models.ForeignKey("battle.Dungeon", related_name="floors", on_delete=models.CASCADE)
    floor = models.IntegerField()

    class Meta:
        unique_together = ('dungeon', 'floor')


class DungeonFloorMonster(BaseModel):
    dungeon_floor = models.ForeignKey("battle.DungeonFloor", related_name="monsters", on_delete=models.CASCADE)
    monster = models.ForeignKey("battle.Monster", on_delete=models.PROTECT)


class DungeonReward(BaseModel):
    dungeon = models.ForeignKey("battle.Dungeon", related_name="rewards", on_delete=models.CASCADE)

    divisor = models.IntegerField()
    group = models.ForeignKey("item.ItemTypePoolGroup", on_delete=models.CASCADE)
    number = models.IntegerField(default=1)


class BattleResult(BaseModel):
    category = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    content = models.JSONField()


# 神獸

class WorldBossTemplate(BaseModel):
    name = models.CharField(max_length=20, unique=True)

    base_attribute = models.IntegerField()
    base_hp = models.IntegerField()
    base_mp = models.IntegerField()

    difficulty = models.FloatField(default=1)


class WorldBossNameBase(BaseModel):
    name = models.CharField(max_length=20)
    category = models.CharField(max_length=10)

    class Meta:
        unique_together = ('name', 'category')


class WorldBoss(BaseModel):
    template = models.ForeignKey("battle.WorldBossTemplate", on_delete=models.PROTECT)
    is_alive = models.BooleanField(default=True)
    location = models.ForeignKey("world.Location", on_delete=models.PROTECT)

    name = models.CharField(max_length=40)
    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)

    hp_max = models.PositiveIntegerField()
    hp = models.PositiveIntegerField()
    mp_max = models.PositiveIntegerField()
    mp = models.PositiveIntegerField()

    abilities = models.ManyToManyField("ability.Ability")


class WorldBossAttribute(BaseModel):
    world_boss = models.ForeignKey("battle.WorldBoss", on_delete=models.CASCADE, related_name="attributes")
    type = models.ForeignKey("world.AttributeType", on_delete=models.PROTECT)
    value = models.IntegerField()

    class Meta:
        unique_together = ('world_boss', 'type')


class WorldBossSkillSetting(BaseSkillSetting):
    world_boss = models.ForeignKey("battle.WorldBoss", on_delete=models.CASCADE, related_name="skill_settings")

# 競技場


class Arena(BaseModel):
    name = models.CharField(max_length=20)
    attribute_type = models.ForeignKey("world.AttributeType", null=True, on_delete=models.PROTECT)

    occupier = models.ForeignKey("chara.Chara", null=True, on_delete=models.SET_NULL)
    occupied_at = models.DateTimeField(null=True)
    occupier_win_count = models.IntegerField(default=0)
