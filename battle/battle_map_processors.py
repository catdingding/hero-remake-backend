from random import choice, choices

from django.db.models import F

from base.utils import add_class, randint
from battle.battle import Battle
from item.models import ItemType, ItemTypePoolGroup
from item.serializers import SimpleItemSerializer
from chara.models import BattleMapTicket, CharaAttribute
from world.models import AttributeType


BATTLE_MAP_PROCESSORS = {}


class BaseBattleMapProcessor():
    map_loot_group_settings = [
        {'id': 1, 'rand': 10000}
    ]

    def __init__(self, chara, battle_map):
        self.chara = chara
        self.location = chara.location
        self.battle_map = battle_map

    def execute(self):
        self.monsters = self.get_monsters()

        battle = Battle(attackers=[self.chara], defenders=self.monsters, element_type=self.location.element_type)
        battle.execute()

        self.win = (battle.winner == 'attacker')

        self.chara.record.total_battle += 1

        if self.win:
            loots = self.get_loots()
            gold = self.get_gold()
            exp = self.get_exp()
            proficiency = self.get_proficiency()
            found_battle_maps = self.find_battle_maps()
        else:
            loots = []
            exp = 0
            gold = 0
            proficiency = 0
            found_battle_maps = []

        battle_chara = battle.find_chara_by_source(self.chara)

        self.chara.hp = battle_chara.hp
        self.chara.mp = battle_chara.mp
        if self.chara.health > 0 and randint(1, 100) == 1:
            self.chara.health -= 1
        self.chara.gold += gold
        self.chara.proficiency += proficiency
        self.chara.gain_exp(exp)
        self.chara.get_items('bag', loots)
        CharaAttribute.objects.filter(
            chara=self.chara, type_id=self.chara.job.attribute_type_id
        ).update(proficiency=F('proficiency') + proficiency)
        BattleMapTicket.objects.filter(
            chara=self.chara, battle_map__in=found_battle_maps
        ).update(value=F('value') + 1)

        self.chara.save()

        self.chara.record.save()

        return {
            'winner': battle.winner,
            'logs': battle.logs,
            'loots': SimpleItemSerializer(loots, many=True).data,
            'gold': gold,
            'proficiency': proficiency,
            'exp': exp,
            'messages': []
        }

    def get_monsters(self):
        number = self.get_monster_number()
        monsters = self.battle_map.monsters.all()
        weights = [m.weight for m in monsters]

        return choices([m.monster for m in monsters], k=number, weights=weights)

    def get_loots(self):
        return self.get_monster_loots() + self.get_map_loots()

    def get_monster_loots(self):
        return []

    def get_map_loots(self):
        loots = []
        for group_setting in self.map_loot_group_settings:
            if randint(1, group_setting['rand']) == 1:
                group = ItemTypePoolGroup.objects.get(id=group_setting['id'])
                loots.extend(group.pick())

        return loots

    def get_monster_number(self):
        return choices([1, 2], k=1, weights=[20, 1])[0]

    def get_proficiency(self):
        return self.battle_map.proficiency * len(self.monsters)

    def get_gold(self):
        return sum(monster.gold for monster in self.monsters)

    def get_exp(self):
        return sum(monster.exp for monster in self.monsters)

    def find_battle_maps(self):
        battle_maps = []
        """ 隨機地圖 """
        # 財寶洞窟
        if randint(1, 30) == 1:
            battle_maps.append(8)
        # 黃金宮殿
        if randint(1, 300) == 1:
            battle_maps.append(9)
        # 藍天之下
        if randint(1, 2500) == 1:
            battle_maps.append(10)
        # 星空下的夜
        if randint(1, 20000) == 1:
            battle_maps.append(11)
        # 暗黑雪原
        if randint(1, 1000) == 1:
            battle_maps.append(16)

        """ 戰數地圖 """
        if self.chara.record.total_battle % 100 == 0:
            battle_maps.append(13)
        if self.chara.record.total_battle % 300 == 0:
            battle_maps.append(14)
        if self.chara.record.total_battle % 600 == 0:
            battle_maps.append(15)
        if self.chara.record.total_battle % 3000 == 0:
            battle_maps.append(11)
        if self.chara.record.total_battle % 10000 == 0:
            battle_maps.append(12)

        return battle_maps


# 草原
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_1(BaseBattleMapProcessor):
    id = 1


# 沼地
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_2(BaseBattleMapProcessor):
    id = 2


# 森林
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_3(BaseBattleMapProcessor):
    id = 3


# 高塔
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_4(BaseBattleMapProcessor):
    id = 4


# 廢城
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_5(BaseBattleMapProcessor):
    id = 5


# 禁地
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_6(BaseBattleMapProcessor):
    id = 6


# 魔王城
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_7(BaseBattleMapProcessor):
    id = 7


# 財寶洞窟
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_8(BaseBattleMapProcessor):
    id = 8

    def get_gold(self):
        return randint(1, 200000)


# 黃金宮殿
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_9(BaseBattleMapProcessor):
    id = 9

    def get_gold(self):
        return randint(1, 2000000)


# 藍天之下
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_10(BaseBattleMapProcessor):
    id = 10

    def find_battle_maps(self):
        battle_maps = super().find_battle_maps()
        # 星空下的夜
        if randint(1, 12) == 1:
            battle_maps.append(11)

        return battle_maps


# 星空下的夜
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_11(BaseBattleMapProcessor):
    id = 11

    map_loot_group_settings = [
        {'id': 1, 'rand': 1}
    ]


# 傳說密地
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_12(BaseBattleMapProcessor):
    id = 12

    def get_map_loots(self):
        return super().get_map_loots() + ItemType.objects.get(id=482).make(1)


# 冒險者的試煉
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_13(BaseBattleMapProcessor):
    id = 13

    def get_gold(self):
        return randint(1, 250000) + 250000


# 勇者的試練
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_14(BaseBattleMapProcessor):
    id = 14

    def get_gold(self):
        return randint(1, 500000) + 500000


# 英雄的試練
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_15(BaseBattleMapProcessor):
    id = 15

    def get_gold(self):
        return randint(1, 1000000) + 1000000


# 暗黑雪原
@add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_16(BaseBattleMapProcessor):
    id = 16

    def get_gold(self):
        return randint(1, 2000000)

    def execute(self):
        result = super().execute()

        attribute_type = choice(AttributeType.objects.all())

        chara_attr = self.chara.attributes.get(type=attribute_type)
        chara_attr.limit += 1
        chara_attr.save()

        result['messages'].append(f"{attribute_type.name}上限提升了1點")

        return result
