from random import choice, choices

from django.db.models import F

from base.utils import add_class, randint
from battle.utils import get_event_item_type
from battle.battle import Battle
from item.models import ItemType, ItemTypePoolGroup, ItemTypePool
from item.serializers import SimpleItemSerializer
from chara.models import BattleMapTicket, CharaAttribute
from world.models import AttributeType

from system.utils import push_log

BATTLE_MAP_PROCESSORS = {}


class AttributeUpgradeMixin:
    def execute(self):
        result = super().execute()

        if self.win:
            attribute_type = choice(AttributeType.objects.all())

            chara_attr = self.chara.attributes.get(type=attribute_type)
            chara_attr.limit += 1
            chara_attr.save()

            result['messages'].append(f"{attribute_type.name}上限提升了1點")

        return result


class BaseBattleMapProcessor():
    # ItemTypePoolGroup
    map_loot_group_settings = [
        {'id': 1, 'rand': 10000}
    ]
    # ItemType
    map_loot_settings = []

    def __init__(self, chara, battle_map):
        self.chara = chara
        self.location = chara.location
        self.battle_map = battle_map

    def execute(self):
        self.monsters = self.get_monsters()

        battle = Battle(attackers=[self.chara], defenders=self.monsters,
                        battle_type='pve', element_type=self.location.element_type)
        battle.execute()

        self.win = (battle.winner == 'attacker')

        self.chara.record.total_battle += 1
        self.chara.record.today_battle += 1

        if self.win:
            self.chara.record.world_monster_quest_counter += len(self.monsters)
            if self.chara.country is not None and self.chara.country == self.location.country:
                self.chara.record.country_monster_quest_counter += len(self.monsters)

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

        if loots:
            log_loots = [x for x in loots if '原料' not in x.type.name and '建國之石' not in x.type.name]
            if log_loots:
                log_loots = '、'.join(f'{x.type.name}*{x.number}' for x in log_loots)
                push_log("打寶", f"{self.chara.name}於{self.battle_map.name}獲得了{log_loots}")
        if battle.winner == 'defender':
            push_log("陣亡", f"{self.chara.name}於{self.battle_map.name}被{'與'.join({x.name for x in self.monsters})}打到在地上磨擦")

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

    def rand_loot(self, n):
        # 奧義類型13:獲得額外金錢與掉寶
        n = n * (1 - self.chara.equipped_ability_type_power(13) * 0.1)
        n = max(int(n), 1)
        return randint(1, n) == 1

    def get_loots(self):
        return self.get_common_loots() + self.get_monster_loots() + self.get_map_loots() + self.get_event_loots() + \
            self.get_ability_loots()

    def get_common_loots(self):
        loots = []

        # 建國之石
        rand = 2000
        if self.chara.country_id is None:
            rand = 500

        if self.rand_loot(rand):
            loots.extend(ItemType.objects.get(id=472).make(1))

        return loots

    def get_monster_loots(self):
        return []

    def get_map_loots(self):
        loots = []
        # ItemTypePoolGroup
        for group_setting in self.map_loot_group_settings:
            if self.rand_loot(group_setting['rand']):
                group = ItemTypePoolGroup.objects.get(id=group_setting['id'])
                loots.extend(group.pick())

        # ItemType
        for setting in self.map_loot_settings:
            if self.rand_loot(setting['rand']):
                loots.extend(ItemType.objects.get(id=setting['id']).make(1))

        return loots

    def get_event_loots(self):
        loots = []

        event_item_type = get_event_item_type()

        if event_item_type is not None and randint(1, 250) == 1:
            loots.extend(event_item_type.make(1))

        return loots

    def get_ability_loots(self):
        loots = []

        if self.id in [5, 6, 7]:
            # 奧義類型38:尋找原料
            if self.chara.has_equipped_ability_type(38) and randint(1, self.chara.equipped_ability_type_power(38)) == 1:
                group = ItemTypePoolGroup.objects.get(id=6)
                loots.extend(group.pick())

        if self.chara.has_equipped_ability_type(36) and randint(1, self.chara.equipped_ability_type_power(36)) == 1:
            pool = ItemTypePool.objects.get(id=8)
            loots.extend(pool.pick())

        return loots

    def get_monster_number(self):
        return choices([1, 2], k=1, weights=[20, 1])[0]

    def get_proficiency(self):
        # 奧義類型22:獲得額外熟練與經驗
        return self.battle_map.proficiency * len(self.monsters) + self.chara.equipped_ability_type_power(22)

    def get_gold(self):
        gold = sum(monster.gold for monster in self.monsters)
        # 奧義類型13:獲得額外金錢與掉寶
        if self.chara.equipped_ability_type_power(13) >= randint(1, 10):
            gold *= 3
        return gold

    def get_exp(self):
        # 奧義類型22:獲得額外熟練與經驗
        return sum(monster.exp for monster in self.monsters) * int(1 + self.chara.equipped_ability_type_power(22) * 2)

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
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_1(BaseBattleMapProcessor):
    id = 1

    map_loot_group_settings = []


# 沼地
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_2(BaseBattleMapProcessor):
    id = 2

    map_loot_group_settings = []


# 森林
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_3(BaseBattleMapProcessor):
    id = 3
    map_loot_settings = [
        {'id': 1018, 'rand': 1000}
    ]


# 高塔
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_4(BaseBattleMapProcessor):
    id = 4
    map_loot_settings = [
        {'id': 1019, 'rand': 1000}
    ]

    map_loot_group_settings = [
        {'id': 1, 'rand': 8000}
    ]


# 廢城
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_5(BaseBattleMapProcessor):
    id = 5
    map_loot_settings = [
        {'id': 1020, 'rand': 1000}
    ]

    map_loot_group_settings = [
        {'id': 1, 'rand': 7000},
        {'id': 6, 'rand': 400}
    ]


# 禁地
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_6(BaseBattleMapProcessor):
    id = 6

    map_loot_group_settings = [
        {'id': 1, 'rand': 6000},
        {'id': 6, 'rand': 400}
    ]

    def get_monster_loots(self):
        loots = super().get_monster_loots()
        for monster in self.monsters:
            # 魔王
            if monster.id == 41:
                if self.rand_loot(250):
                    group = ItemTypePoolGroup.objects.get(id=7)
                    loots.extend(group.pick())

        return loots

    def execute(self):
        result = super().execute()

        if self.win:
            for monster in self.monsters:
                # 魔王
                if monster.id == 41:
                    attribute_type = choice(AttributeType.objects.all())

                    chara_attr = self.chara.attributes.get(type=attribute_type)
                    chara_attr.limit += 1
                    chara_attr.save()

                    result['messages'].append(f"{attribute_type.name}上限提升了1點")

        return result


# 魔王城
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_7(BaseBattleMapProcessor):
    id = 7

    map_loot_group_settings = [
        {'id': 1, 'rand': 10000},
        {'id': 6, 'rand': 400},
        {'id': 8, 'rand': 500}
    ]


# 財寶洞窟
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_8(BaseBattleMapProcessor):
    id = 8

    def get_gold(self):
        return randint(1, 200000)


# 黃金宮殿
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_9(BaseBattleMapProcessor):
    id = 9

    def get_gold(self):
        return randint(1, 2000000)


# 藍天之下
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_10(BaseBattleMapProcessor):
    id = 10

    def find_battle_maps(self):
        battle_maps = super().find_battle_maps()
        # 星空下的夜
        # 奧義類型30:天運
        rand = 12 - self.chara.equipped_ability_type_power(30)
        if randint(1, rand) == 1:
            battle_maps.append(11)

        return battle_maps


# 星空下的夜
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_11(BaseBattleMapProcessor):
    id = 11

    map_loot_group_settings = [
        {'id': 1, 'rand': 1}
    ]


# 傳說密地
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_12(BaseBattleMapProcessor):
    id = 12

    def get_map_loots(self):
        return super().get_map_loots() + ItemType.objects.get(id=482).make(1)


# 冒險者的試煉
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_13(BaseBattleMapProcessor):
    id = 13

    def get_gold(self):
        return randint(1, 250000) + 250000


# 勇者的試練
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_14(BaseBattleMapProcessor):
    id = 14

    def get_gold(self):
        return randint(1, 500000) + 500000


# 英雄的試練
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_15(AttributeUpgradeMixin, BaseBattleMapProcessor):
    id = 15

    def get_gold(self):
        return randint(1, 1000000) + 1000000


# 暗黑雪原
@ add_class(BATTLE_MAP_PROCESSORS)
class BattleMapProcessor_16(AttributeUpgradeMixin, BaseBattleMapProcessor):
    id = 16

    def get_gold(self):
        return randint(1, 2000000)
