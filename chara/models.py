from faulthandler import is_enabled
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import localtime
from django.conf import settings

from rest_framework.exceptions import ValidationError

import time
import hashlib
import os
from datetime import timedelta
import random
import functools

from base.models import BaseModel, BaseSkillSetting
from base.utils import get_items, lose_items, sftp_put_fo
from ability.models import Ability
from chara.utils import process_avatar
from world.models import AttributeType, SlotType
from battle.models import BattleMap


class Chara(BaseModel):
    user = models.ForeignKey("user.User", related_name="charas", on_delete=models.CASCADE)
    name = models.CharField(max_length=30, unique=True)
    avatar_version = models.IntegerField(default=0)

    next_action_time = models.DateTimeField(default=localtime)

    location = models.ForeignKey("world.Location", on_delete=models.PROTECT)
    country = models.ForeignKey("country.Country", null=True,
                                related_name="citizens", on_delete=models.SET_NULL)
    team = models.ForeignKey("team.Team", null=True, related_name="members", on_delete=models.SET_NULL)

    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)
    job = models.ForeignKey("job.Job", on_delete=models.PROTECT)

    exp = models.PositiveIntegerField(default=0)
    proficiency = models.BigIntegerField(default=0)
    pvp_points = models.IntegerField(default=1000)

    gold = models.BigIntegerField(default=0)

    main_ability = models.ForeignKey("ability.Ability", null=True,
                                     related_name="main_ability_charas", on_delete=models.PROTECT)
    job_ability = models.ForeignKey("ability.Ability", null=True,
                                    related_name="job_ability_charas", on_delete=models.PROTECT)
    live_ability = models.ForeignKey("ability.Ability", null=True,
                                     related_name="live_ability_charas", on_delete=models.PROTECT)

    partner = models.OneToOneField("chara.CharaPartner", null=True,
                                   related_name="selected_partner_of", on_delete=models.SET_NULL)
    title = models.OneToOneField("chara.CharaTitle", null=True,
                                 related_name="selected_title_of", on_delete=models.SET_NULL)

    health = models.IntegerField(default=100)

    hp_max = models.PositiveIntegerField()
    hp = models.PositiveIntegerField()
    mp_max = models.PositiveIntegerField()
    mp = models.PositiveIntegerField()

    luck_base = models.PositiveIntegerField(default=1000)

    bag_items = models.ManyToManyField("item.Item", related_name="bag_item_chara")
    storage_items = models.ManyToManyField("item.Item", related_name="storage_item_chara")
    abilities = models.ManyToManyField("ability.Ability")

    bag_item_limit = models.IntegerField(default=15)
    storage_item_limit = models.IntegerField(default=15)

    # member
    member_point_paid = models.PositiveIntegerField(default=0)
    member_point_free = models.PositiveIntegerField(default=0)

    has_cold_down_bonus = models.BooleanField(default=False)
    has_quest_bonus = models.BooleanField(default=False)
    has_auto_heal = models.BooleanField(default=False)

    has_transfer_permission = models.BooleanField(default=True)

    @property
    def level(self):
        return self.exp // 100 + 1

    @property
    def luck(self):
        n = f"{round(time.time()) // 3600}{self.id}"
        n = int.from_bytes(hashlib.sha256(n.encode("utf-8")).digest(), 'big') % 10

        if n <= 2:
            return int(self.luck_base * 0.5)
        elif n >= 7:
            return int(self.luck_base * 1.5)
        return self.luck_base

    @property
    def luck_sigmoid(self):
        n = self.luck
        return n / (n + 1000)

    @cached_property
    def attrs(self):
        return {x.type.en_name: x for x in self.attributes.all().select_related('type')}

    @cached_property
    def equipped_ability_types(self):
        abilities = []
        for slot in self.slots.all().values('item__equipment__ability_1', 'item__equipment__ability_2'):
            abilities.append(slot['item__equipment__ability_1'])
            abilities.append(slot['item__equipment__ability_2'])
        abilities.append(self.main_ability_id)
        abilities.append(self.job_ability_id)
        abilities.append(self.live_ability_id)
        abilities = list(filter(None, abilities))

        return {
            ability.type_id: ability
            for ability in sorted(Ability.objects.filter(id__in=abilities), key=lambda x: x.power)
        }

    def has_equipped_ability_type(self, type_id):
        return type_id in self.equipped_ability_types

    def equipped_ability_type_power(self, type_id):
        try:
            return self.equipped_ability_types[type_id].power
        except KeyError:
            return 0

    @cached_property
    def buff_effects(self):
        return {
            buff.type.effect_id: buff.type
            for buff in sorted(
                self.buffs.filter(due_time__gt=localtime()).select_related('type'),
                key=lambda x: x.type.power
            )
        }

    def buff_effect_power(self, effect_id):
        try:
            return self.buff_effects[effect_id].power
        except KeyError:
            return 0

    @property
    def hp_limit(self):
        limit = self.attrs['str'].limit * 5 + self.attrs['vit'].limit * 10 + self.attrs['men'].limit * 3
        return max(50, limit)

    @property
    def mp_limit(self):
        limit = self.attrs['int'].limit * 5 + self.attrs['men'].limit * 3 + 200
        return max(10, limit)

    def init(self):
        CharaAttribute.objects.bulk_create([
            CharaAttribute(chara=self, type=attr_type, value=30, limit=200)
            for attr_type in AttributeType.objects.all()
        ])
        CharaSlot.objects.bulk_create([CharaSlot(chara=self, type=slot_type) for slot_type in SlotType.objects.all()])
        CharaIntroduction.objects.create(chara=self)
        CharaConfig.objects.create(chara=self)
        CharaCustomTitle.objects.create(chara=self)
        CharaHome.objects.create(chara=self, chars=[''] * 900)
        CharaRecord.objects.create(chara=self)
        BattleMapTicket.objects.bulk_create([
            BattleMapTicket(chara=self, battle_map=battle_map)
            for battle_map in BattleMap.objects.filter(need_ticket=True)
        ])

    def set_avatar(self, file):
        fo = process_avatar(file)
        sftp_put_fo(fo, os.path.join(settings.CHARA_AVATAR_PATH, f"{self.id}.jpg"))
        Chara.objects.filter(id=self.id).update(avatar_version=models.F('avatar_version') + 1)

    @property
    def basic_time_cost(self):
        if self.has_cold_down_bonus:
            cost = 15
        else:
            cost = 20
        return cost

    def set_next_action_time(self, n=1):
        self.next_action_time = max(
            self.next_action_time,
            localtime() - timedelta(hours=24)
        ) + timedelta(seconds=n * self.basic_time_cost)

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
                if attr.value >= attr.limit or (attr.value >= 1800 and attr.type_id != self.job.attribute_type_id):
                    continue

                attr.value += random.randint(0, 1)

        self.hp_max = min(self.hp_max, self.hp_limit)
        self.mp_max = min(self.mp_max, self.mp_limit)

        CharaAttribute.objects.bulk_update(attrs.values(), fields=['value'])

    def get_items(self, kind, *args, **kwargs):
        assert kind in ['bag', 'storage']
        field = getattr(self, kind + '_items')
        limit = getattr(self, kind + '_item_limit')

        return get_items(field, limit, *args, **kwargs)

    def lose_items(self, kind, *args, **kwargs):
        assert kind in ['bag', 'storage']
        field = getattr(self, kind + '_items')

        return lose_items(field, *args, **kwargs)

    def lose_gold(self, number):
        if self.gold < number:
            raise ValidationError("金錢不足")
        self.gold -= number

    def lose_proficiency(self, number):
        if self.proficiency < number:
            raise ValidationError("熟練不足")
        self.proficiency -= number

    def lose_member_point(self, cost, need_paid=False):
        if not need_paid:
            pay_with_free = min(cost, self.member_point_free)
            self.member_point_free -= pay_with_free
            cost -= pay_with_free
        if self.member_point_paid < cost:
            raise ValidationError("點數不足")
        self.member_point_paid -= cost


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
    item = models.ForeignKey("item.Item", null=True, unique=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ('chara', 'type')


class CharaPartner(BaseModel):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE, related_name="partners")

    target_monster = models.ForeignKey("battle.Monster", null=True, on_delete=models.CASCADE)
    target_chara = models.ForeignKey("chara.Chara", null=True, on_delete=models.CASCADE)
    target_npc = models.ForeignKey("npc.NPC", null=True, on_delete=models.CASCADE)

    due_time = models.DateTimeField()

    class Meta:
        unique_together = (('chara', 'target_monster'), ('chara', 'target_chara'), ('chara', 'target_npc'))


class CharaSkillSetting(BaseSkillSetting):
    chara = models.ForeignKey("chara.Chara", on_delete=models.CASCADE, related_name="skill_settings")


class CharaBuffEffect(BaseModel):
    name = models.CharField(max_length=20)


class CharaBuffType(BaseModel):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=100)

    effect = models.ForeignKey("chara.CharaBuffEffect", on_delete=models.CASCADE)
    power = models.IntegerField()


class CharaBuff(BaseModel):
    chara = models.ForeignKey("chara.Chara", related_name="buffs", on_delete=models.CASCADE)
    type = models.ForeignKey("chara.CharaBuffType", on_delete=models.CASCADE)
    due_time = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('chara', 'type')


class CharaAchievementCategory(BaseModel):
    name = models.CharField(max_length=20, unique=True)


class CharaAchievementType(BaseModel):
    category = models.ForeignKey("chara.CharaAchievementCategory", on_delete=models.CASCADE)
    title_type = models.ForeignKey("chara.CharaTitleType", null=True, on_delete=models.SET_NULL)
    requirement = models.BigIntegerField()
    name = models.CharField(max_length=30, unique=True)
    need_announce = models.BooleanField(default=False)


class CharaAchievementCounter(BaseModel):
    chara = models.ForeignKey("chara.Chara", related_name="achievement_counters", on_delete=models.CASCADE)
    category = models.ForeignKey("chara.CharaAchievementCategory", on_delete=models.CASCADE)
    value = models.BigIntegerField(default=0)

    class Meta:
        unique_together = ('chara', 'category')


class CharaAchievement(BaseModel):
    chara = models.ForeignKey("chara.Chara", related_name="achievements", on_delete=models.CASCADE)
    type = models.ForeignKey("chara.CharaAchievementType", on_delete=models.CASCADE)

    class Meta:
        unique_together = ('chara', 'type')


class CharaTitleType(BaseModel):
    name = models.CharField(max_length=20, unique=True)


class CharaTitle(BaseModel):
    chara = models.ForeignKey("chara.Chara", related_name="titles", on_delete=models.CASCADE)
    type = models.ForeignKey("chara.CharaTitleType", on_delete=models.CASCADE)

    class Meta:
        unique_together = ('chara', 'type')


class CharaCustomTitle(BaseModel):
    chara = models.OneToOneField("chara.Chara", on_delete=models.CASCADE, related_name="custom_title")
    name = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=20, blank=True)

    due_time = models.DateTimeField(default=localtime)


class CharaFarm(BaseModel):
    chara = models.ForeignKey("chara.Chara", related_name="farms", on_delete=models.CASCADE)
    item = models.ForeignKey("item.Item", null=True, on_delete=models.SET_NULL)
    due_time = models.DateTimeField(null=True)


class CharaHome(BaseModel):
    chara = models.OneToOneField("chara.Chara", on_delete=models.CASCADE, related_name="home")
    chars = models.JSONField()


class CharaRecord(BaseModel):
    chara = models.OneToOneField("chara.Chara", on_delete=models.CASCADE, related_name="record")

    total_battle = models.IntegerField(default=0)

    level_down_count = models.IntegerField(default=0)

    today_battle = models.IntegerField(default=0)

    world_monster_quest_counter = models.IntegerField(default=0)
    country_monster_quest_counter = models.IntegerField(default=0)


class CharaIntroduction(BaseModel):
    chara = models.OneToOneField("chara.Chara", on_delete=models.CASCADE, related_name="introduction")
    content = models.TextField(blank=True)


class CharaConfig(BaseModel):
    THEME_CHOICES = [
        ('light', 'light'),
        ('dark', 'dark'),
    ]

    chara = models.OneToOneField("chara.Chara", on_delete=models.CASCADE, related_name="config")
    background = models.CharField(max_length=255, blank=True)
    theme = models.CharField(max_length=10, default='light', choices=THEME_CHOICES)

    default_autofight_status = models.BooleanField(default=False)
    use_image_background = models.BooleanField(default=True)


class BattleMapTicket(BaseModel):
    chara = models.ForeignKey("chara.Chara", related_name="battle_map_tickets", on_delete=models.CASCADE)
    battle_map = models.ForeignKey("battle.BattleMap", on_delete=models.CASCADE)
    value = models.IntegerField(default=0)
