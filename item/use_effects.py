from random import choice

from django.db.models import F
from rest_framework.exceptions import ValidationError
from django.utils.timezone import localtime
from datetime import timedelta

from world.models import AttributeType
from ability.models import Ability
from battle.models import BattleMap, Monster
from item.models import ItemTypePoolGroup
from chara.models import BattleMapTicket, CharaBuff, CharaBuffType, CharaPartner, Chara
from npc.models import NPC
from base.utils import add_class
from chara.achievement import update_achievement_counter
from system.utils import push_log

USE_EFFECT_CLASSES = {}


class BaseUseEffect():
    def __init__(self, item, n, chara):
        self.item = item
        self.type = item.type
        self.n = n
        self.chara = chara


# 熟練之書
@add_class(USE_EFFECT_CLASSES)
class UseEffect_1(BaseUseEffect):
    id = 1

    def execute(self):
        value = self.type.power * self.n
        self.chara.proficiency += value
        self.chara.save()

        return f"使用了{self.n}個{self.type.name}，獲得了{value}點熟練。"


# 屬性熟書
@add_class(USE_EFFECT_CLASSES)
class UseEffect_2(BaseUseEffect):
    id = 2

    def execute(self):
        value = self.type.power * self.n
        chara_attr = self.chara.attributes.get(type=self.type.attribute_type)
        chara_attr.proficiency += value
        if chara_attr.proficiency > 999999:
            raise ValidationError("使用上限為999999")
        chara_attr.save()

        return f"使用了{self.n}個{self.type.name}，獲得了{value}點{self.type.attribute_type.class_name}熟練。"


# 提升屬性上限
@add_class(USE_EFFECT_CLASSES)
class UseEffect_3(BaseUseEffect):
    id = 3

    def execute(self):
        value = self.type.power * self.n
        if self.type.use_effect_param == 0:
            maxima = 500
        elif self.type.use_effect_param == 1:
            maxima = 9999

        attribute_type = self.type.attribute_type
        if attribute_type is None:
            attribute_type = choice(AttributeType.objects.all())

        chara_attr = self.chara.attributes.get(type=attribute_type)
        if maxima < chara_attr.limit + value and self.type.attribute_type is not None:
            raise ValidationError("超過使用上限")
        chara_attr.limit = max(chara_attr.limit, chara_attr.limit + value)
        chara_attr.save()

        return f"使用了{self.n}個{self.type.name}，{attribute_type.name}上限變為{chara_attr.limit}點。"


# 轉屬道具
@add_class(USE_EFFECT_CLASSES)
class UseEffect_4(BaseUseEffect):
    id = 4

    def execute(self):
        self.chara.element_type = self.type.element_type
        self.chara.save()
        return f"使用了{self.type.name}，角色屬性變更為{self.type.element_type.name}屬性。"


# 寶箱
@add_class(USE_EFFECT_CLASSES)
class UseEffect_5(BaseUseEffect):
    id = 5

    def execute(self):
        group = ItemTypePoolGroup.objects.get(id=self.type.use_effect_param)
        items = group.pick(self.n)

        self.chara.get_items('bag', items)
        items_name = '、'.join(f'{x.name}*{x.number}' for x in items)
        push_log("寶箱", f"{self.chara.name}使用了{self.n}個{self.type.name}，獲得了{items_name}。")
        # 開寶箱次數
        update_achievement_counter(self.chara.id, 7, self.n, 'increase')
        return f"使用了{self.n}個{self.type.name}，獲得了{items_name}。"


# 地圖入場券
@add_class(USE_EFFECT_CLASSES)
class UseEffect_6(BaseUseEffect):
    id = 6

    def execute(self):
        BattleMapTicket.objects.filter(
            chara=self.chara, battle_map=self.type.use_effect_param
        ).update(value=F('value') + self.n)
        battle_map_name = BattleMap.objects.get(id=self.type.use_effect_param).name
        return f"使用了{self.n}個{self.type.name}，獲得了{self.n}次進入{battle_map_name}的機會。"


# 降級
@add_class(USE_EFFECT_CLASSES)
class UseEffect_7(BaseUseEffect):
    id = 7

    def execute(self):
        if self.type.use_effect_param == 0 and (self.n + self.chara.record.level_down_count) > 50:
            raise ValidationError("每次轉職僅可用地獄草下降50等", 400)
        if self.n * 100 > self.chara.exp:
            raise ValidationError("最多僅可降低至1級", 400)

        self.chara.exp = max(0, self.chara.exp - self.n * 100)
        self.chara.save()

        self.chara.record.level_down_count += self.n
        self.chara.record.save()

        return f"使用了{self.n}個{self.type.name}，降低了{self.n}級。"


# 寵物成長
@add_class(USE_EFFECT_CLASSES)
class UseEffect_8(BaseUseEffect):
    id = 8

    def execute(self):
        from item.serializers import PetUpgradeSerializer

        if not self.chara.slots.filter(type=4, item__equipment__element_type=self.type.element_type).exists():
            raise ValidationError("未裝備對應屬性的寵物")

        serializer = PetUpgradeSerializer(data={'times': self.n})
        serializer.chara = self.chara
        serializer.is_valid(raise_exception=True)
        serializer.save(no_cost=True)
        return f"使用了{self.n}個{self.type.name}，寵物成長了{self.n}級。"


# 奧義卷軸
@add_class(USE_EFFECT_CLASSES)
class UseEffect_9(BaseUseEffect):
    id = 9

    def execute(self):
        ability = Ability.objects.get(id=self.type.use_effect_param)
        if ability.prerequisite is not None:
            if not self.chara.abilities.filter(pk=ability.prerequisite.pk).exists():
                raise ValidationError("需先學習前置奧義")

        self.chara.abilities.add(ability)
        self.chara.save()

        return f"使用了{self.type.name}，習得了{ability.name}。"


# 擴充背包
@add_class(USE_EFFECT_CLASSES)
class UseEffect_10(BaseUseEffect):
    id = 10

    def execute(self):
        value = self.type.power * self.n
        if self.type.use_effect_param == 0:
            maxima = 35
        elif self.type.use_effect_param == 1:
            maxima = 60

        if self.chara.bag_item_limit + value > maxima:
            raise ValidationError("超過使用上限")

        self.chara.bag_item_limit = self.chara.bag_item_limit + value
        self.chara.save()

        return f"使用了{self.n}個{self.type.name}，背包上限變為{self.chara.bag_item_limit}。"


# 擴充倉庫
@add_class(USE_EFFECT_CLASSES)
class UseEffect_11(BaseUseEffect):
    id = 11

    def execute(self):
        value = self.type.power * self.n

        self.chara.storage_item_limit += value
        if self.chara.storage_item_limit > 10000:
            raise ValidationError("DB的物品表會太大，求你別再擴了……")
        self.chara.save()

        return f"使用了{self.n}個{self.type.name}，倉庫上限變為{self.chara.storage_item_limit}。"


# 贊助點數
@add_class(USE_EFFECT_CLASSES)
class UseEffect_12(BaseUseEffect):
    id = 12

    def execute(self):
        value = self.type.power * self.n

        self.chara.member_point += value
        self.chara.save()

        return f"使用了{self.n}個{self.type.name}，獲得了{value}點贊助點數"


# 角色buff
@add_class(USE_EFFECT_CLASSES)
class UseEffect_13(BaseUseEffect):
    id = 13

    def execute(self):
        hours = self.type.power * self.n

        buff = CharaBuff.objects.filter(chara=self.chara, type=self.type.use_effect_param).first()
        if buff is None:
            buff = CharaBuff(
                chara=self.chara, type_id=self.type.use_effect_param,
                due_time=localtime() + timedelta(hours=hours)
            )
        else:
            buff.due_time = max(buff.due_time, localtime()) + timedelta(hours=hours)

        buff.save()

        buff_type = CharaBuffType.objects.get(id=self.type.use_effect_param)

        # 使用buff道具次數
        update_achievement_counter(self.chara.id, 26, 1, 'increase')

        return f"使用了{self.n}個{self.type.name}，獲得了{hours}小時的{buff_type.name}"


# 同伴召喚-怪
@add_class(USE_EFFECT_CLASSES)
class UseEffect_14(BaseUseEffect):
    id = 14

    def execute(self):
        minutes = self.type.power * self.n

        monster = Monster.objects.get(id=self.type.use_effect_param)
        partner = CharaPartner.objects.filter(chara=self.chara, target_monster=monster).first()
        if partner is None:
            partner = CharaPartner(
                chara=self.chara, target_monster=monster,
                due_time=localtime() + timedelta(minutes=minutes)
            )
        else:
            partner.due_time = max(partner.due_time, localtime()) + timedelta(minutes=minutes)

        partner.save()

        return f"使用了{self.n}個{self.type.name}，獲得了{minutes}分鐘的{monster.name}同伴"


# 同伴召喚-角色
@add_class(USE_EFFECT_CLASSES)
class UseEffect_15(BaseUseEffect):
    id = 15

    def execute(self):
        minutes = self.type.power * self.n

        chara = Chara.objects.get(id=self.type.use_effect_param)
        partner = CharaPartner.objects.filter(chara=self.chara, target_chara=chara).first()
        if partner is None:
            partner = CharaPartner(
                chara=self.chara, target_chara=chara,
                due_time=localtime() + timedelta(minutes=minutes)
            )
        else:
            partner.due_time = max(partner.due_time, localtime()) + timedelta(minutes=minutes)

        partner.save()

        return f"使用了{self.n}個{self.type.name}，獲得了{minutes}分鐘的{chara.name}同伴"


# 同伴召喚-NPC
@add_class(USE_EFFECT_CLASSES)
class UseEffect_16(BaseUseEffect):
    id = 16

    def execute(self):
        minutes = self.type.power * self.n

        npc = NPC.objects.get(id=self.type.use_effect_param)
        partner = CharaPartner.objects.filter(chara=self.chara, target_npc=npc).first()
        if partner is None:
            partner = CharaPartner(
                chara=self.chara, target_npc=npc,
                due_time=localtime() + timedelta(minutes=minutes)
            )
        else:
            partner.due_time = max(partner.due_time, localtime()) + timedelta(minutes=minutes)

        partner.save()

        # 召喚NPC時數
        update_achievement_counter(self.chara.id, 25, minutes, 'increase')

        return f"使用了{self.n}個{self.type.name}，獲得了{minutes}分鐘的{npc.name}同伴"
