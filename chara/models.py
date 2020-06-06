from django.db import models
from django.utils.timezone import localtime
from base.models import BaseModel, BaseBuffType

from datetime import timedelta
import random
import functools


class Chara(BaseModel):
    user = models.ForeignKey("user.User", related_name="charas", on_delete=models.CASCADE)
    name = models.CharField(max_length=30, unique=True)

    next_action_time = models.DateTimeField(default=localtime)

    location = models.ForeignKey("world.Location", on_delete=models.PROTECT)

    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)
    job = models.ForeignKey("job.Job", on_delete=models.PROTECT)

    exp = models.PositiveIntegerField(default=0)
    proficiency = models.PositiveIntegerField(default=0)

    gold = models.PositiveIntegerField(default=0)

    main_ability = models.ForeignKey("ability.Ability", null=True,
                                     related_name="main_ability_charas", on_delete=models.PROTECT)
    job_ability = models.ForeignKey("ability.Ability", null=True,
                                    related_name="job_ability_charas", on_delete=models.PROTECT)

    hp_max = models.PositiveIntegerField()
    hp = models.PositiveIntegerField()
    mp_max = models.PositiveIntegerField()
    mp = models.PositiveIntegerField()

    items = models.ManyToManyField("item.Item", through="chara.CharaItem")
    abilities = models.ManyToManyField("ability.Ability")

    @property
    def level(self):
        return self.exp // 100 + 1

    @property
    @functools.lru_cache()
    def attrs(self):
        return {x.type_id: x for x in self.attributes.all()}

    def hp_limit(self):
        return self.attrs['str'].value * 5 + self.attrs['vit'].value * 10 + self.attrs['men'].value * 3 - 2000

    def mp_limit(self):
        return self.attrs['int'].value * 5 + self.attrs['men'] * 3 - 800

    def set_next_action_time(self, n=1):
        self.next_action_time = localtime() + timedelta(seconds=n * 15)

    def gain_exp(self, exp):
        orig_level = self.level
        self.exp = min(self.exp + exp, 9999)
        self.level_up(self.level - orig_level)

    def level_up(self, n_level):
        if n_level <= 0:
            return

        attrs = self.attrs

        for i in range(n_level):
            self.hp_max += random.randint(0, int(attrs['vit'].value / 40 + attrs['men'].value / 80 + 8))
            self.mp_max += random.randint(0, int(attrs['int'].value / 40 + attrs['men'].value / 80 + 2))
            for attr in attrs.values():
                if attr.value >= attr.limit and attr.attribute_id != self.job.attribute_id:
                    continue

                attr.value += random.randint(0, 1)

        self.hp_max = min(self.hp_max, self.hp_limit)
        self.mp_max = min(self.mp_max, self.mp_limit)

        CharaAttribute.objects.bulk_update(attrs.values())


class CharaAttribute(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE, related_name="attributes")
    type = models.ForeignKey("world.AttributeType", on_delete=models.PROTECT)
    value = models.IntegerField()
    limit = models.IntegerField()

    class Meta:
        unique_together = ('chara', 'type')


class CharaSlot(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE, related_name="slots")
    type = models.ForeignKey("world.SlotType", on_delete=models.CASCADE)
    item = models.ForeignKey("item.Item", null=True, unique=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('chara', 'type')


class CharaItem(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE)
    item = models.ForeignKey("item.Item", unique=True, on_delete=models.CASCADE)


class CharaSkillSetting(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE, related_name="skill_settings")
    skill = models.ForeignKey("job.Skill", on_delete=models.CASCADE)

    hp_percentage = models.PositiveSmallIntegerField()
    mp_percentage = models.PositiveSmallIntegerField()

    priority = models.PositiveSmallIntegerField()


class CharaBuffType(BaseBuffType):
    pass


class CharaBuff(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE)
    type = models.ForeignKey("chara.CharaBuffType", on_delete=models.CASCADE)
    value = models.IntegerField(null=True)
    due_date = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('chara', 'type')


class CharaIntroduction(BaseModel):
    chara = models.OneToOneField("chara.Chara", on_delete=models.CASCADE, related_name="introduction")
    content = models.TextField(blank=True)
