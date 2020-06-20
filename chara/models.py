from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import localtime

from rest_framework.exceptions import APIException

from datetime import timedelta
import random
import functools

from base.models import BaseModel, BaseBuffType
from base.utils import get_items, lose_items


class Chara(BaseModel):
    user = models.ForeignKey("user.User", related_name="charas", on_delete=models.CASCADE)
    name = models.CharField(max_length=30, unique=True)

    next_action_time = models.DateTimeField(default=localtime)

    location = models.ForeignKey("world.Location", on_delete=models.PROTECT)
    country = models.ForeignKey("country.Country", null=True,
                                related_name="citizens", on_delete=models.SET_NULL)

    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)
    job = models.ForeignKey("job.Job", on_delete=models.PROTECT)

    exp = models.PositiveIntegerField(default=0)
    proficiency = models.BigIntegerField(default=0)

    gold = models.BigIntegerField(default=0)

    main_ability = models.ForeignKey("ability.Ability", null=True,
                                     related_name="main_ability_charas", on_delete=models.PROTECT)
    job_ability = models.ForeignKey("ability.Ability", null=True,
                                    related_name="job_ability_charas", on_delete=models.PROTECT)
    live_ability = models.ForeignKey("ability.Ability", null=True,
                                     related_name="live_ability_charas", on_delete=models.PROTECT)

    hp_max = models.PositiveIntegerField()
    hp = models.PositiveIntegerField()
    mp_max = models.PositiveIntegerField()
    mp = models.PositiveIntegerField()

    bag_items = models.ManyToManyField("item.Item", related_name="bag_item_chara")
    storage_items = models.ManyToManyField("item.Item", related_name="storage_item_chara")
    abilities = models.ManyToManyField("ability.Ability")

    @property
    def level(self):
        return self.exp // 100 + 1

    @cached_property
    def attrs(self):
        return {x.type_id: x for x in self.attributes.all()}

    @property
    def hp_limit(self):
        return self.attrs['str'].value * 5 + self.attrs['vit'].value * 10 + self.attrs['men'].value * 3 - 2000

    @property
    def mp_limit(self):
        return self.attrs['int'].value * 5 + self.attrs['men'].value * 3 - 800

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
                if attr.value >= attr.limit or (attr.value > 1200 and attr.type_id != self.job.attribute_id):
                    continue

                attr.value += random.randint(0, 1)

        self.hp_max = min(self.hp_max, self.hp_limit)
        self.mp_max = min(self.mp_max, self.mp_limit)

        CharaAttribute.objects.bulk_update(attrs.values())

    def get_items(self, kind, *args, **kwargs):
        assert kind in ['bag', 'storage']
        field = getattr(self, kind + '_items')

        return get_items(field, *args, **kwargs)

    def lose_items(self, kind, *args, **kwargs):
        assert kind in ['bag', 'storage']
        field = getattr(self, kind + '_items')

        return lose_items(field, *args, **kwargs)

    def lose_gold(self, number):
        if self.gold < number:
            raise APIException("金錢不足")
        self.gold -= number


class CharaAttribute(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE, related_name="attributes")
    type = models.ForeignKey("world.AttributeType", on_delete=models.PROTECT)
    value = models.IntegerField()
    limit = models.IntegerField()
    proficiency = models.IntegerField(default=0)

    class Meta:
        unique_together = ('chara', 'type')


class CharaSlot(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE, related_name="slots")
    type = models.ForeignKey("world.SlotType", on_delete=models.CASCADE)
    item = models.ForeignKey("item.Item", null=True, unique=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('chara', 'type')


class CharaSkillSetting(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE, related_name="skill_settings")
    skill = models.ForeignKey("job.Skill", on_delete=models.CASCADE)

    hp_percentage = models.PositiveSmallIntegerField()
    mp_percentage = models.PositiveSmallIntegerField()

    order = models.IntegerField()


class CharaBuffType(BaseBuffType):
    pass


class CharaBuff(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE)
    type = models.ForeignKey("chara.CharaBuffType", on_delete=models.CASCADE)
    value = models.IntegerField(null=True)
    due_date = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('chara', 'type')


class CharaRecord(BaseModel):
    chara = models.OneToOneField("chara.Chara", on_delete=models.CASCADE, related_name="record")

    total_battle = models.IntegerField(default=0)
    monthly_level_up = models.IntegerField(default=0)


class CharaIntroduction(BaseModel):
    chara = models.OneToOneField("chara.Chara", on_delete=models.CASCADE, related_name="introduction")
    content = models.TextField(blank=True)
