from random import choice

from django.db.models import F
from rest_framework.exceptions import ValidationError

from world.models import AttributeType
from ability.models import Ability
from battle.models import BattleMap
from item.models import ItemTypePoolGroup
from chara.models import BattleMapTicket
from base.utils import add_class

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
        chara_attr.proficiency = min(999999, chara_attr.proficiency + value)
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
        chara_attr.limit = max(chara_attr.limit, min(chara_attr.limit + value, maxima))
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
        items = []
        group = ItemTypePoolGroup.objects.get(id=self.type.use_effect_param)
        for i in range(self.n):
            items.extend(group.pick())

        self.chara.get_items('bag', items)
        items_name = "、".join(item.type.name for item in items)
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

        self.chara.bag_item_limit = min(maxima, self.chara.bag_item_limit + value)
        self.chara.save()

        return f"使用了{self.n}個{self.type.name}，背包上限變為{self.chara.bag_item_limit}。"


# 擴充倉庫
@add_class(USE_EFFECT_CLASSES)
class UseEffect_11(BaseUseEffect):
    id = 11

    def execute(self):
        value = self.type.power * self.n

        self.chara.storage_item_limit += value
        self.chara.save()

        return f"使用了{self.n}個{self.type.name}，倉庫上限變為{self.chara.storage_item_limit}。"
