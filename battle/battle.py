from random import choice, choices
from collections import Counter

from base.utils import randint
from battle.models import Monster, WorldBoss
from chara.models import Chara
from item.models import Equipment


class EmptyEquipment:
    attack = 0
    defense = 0
    weight = 0

    ability_1 = None
    ability_2 = None

    element_type_id = None


class Battle:
    def __init__(self, attackers, defenders, battle_type, element_type=None, difficulty=1):
        assert battle_type in ['pvp', 'pve', 'dungeon', 'world_boss']
        self.battle_type = battle_type
        self.element_type = element_type
        self.difficulty = difficulty
        self.charas = [BattleChara(x, battle=self, team='attacker') for x in attackers] + \
            [BattleChara(x, battle=self, team='defender') for x in defenders]
        self.rename_charas()

        self.executed = False
        self.logs = []
        self.rounds = 0

        self.actions = 0
        self.max_actions = len(self.charas) * 2 * self.max_rounds

    @property
    def max_rounds(self):
        return 400

    @property
    def winner(self):
        if not any(chara.team == 'attacker' for chara in self.alive_charas):
            return "defender"
        elif not any(chara.team == 'defender' for chara in self.alive_charas):
            return "attacker"
        else:
            return "draw"

    def rename_charas(self):
        total_counter = Counter([x.name for x in self.charas])
        current_counter = Counter()

        for chara in self.charas:
            if total_counter[chara.name] != 1:
                current_counter[chara.name] += 1
                chara.name = f"{chara.name}{current_counter[chara.name]}"

    def execute(self):
        assert not self.executed
        self.executed = True
        index = 0

        while True:
            self.logs.append({'actions': [], 'index': index})
            index += 1

            act_chara = self.get_act_chara()
            if act_chara is None:
                self.next_round()
            else:
                act_chara.take_action()
                self.actions += 1
                self.logs[-1]['charas'] = [chara.profile for chara in self.charas]

            if self.winner != 'draw' or self.rounds >= self.max_rounds or self.actions >= self.max_actions:
                break

    @property
    def alive_charas(self):
        return [chara for chara in self.charas if chara.hp > 0]

    def next_round(self):
        self.rounds += 1

        for chara in self.alive_charas:
            chara.increase_action_points()

    def get_act_chara(self):
        max_action_points = max([c.action_points for c in self.alive_charas])
        if max_action_points < 1000:
            return None
        else:
            return choice([c for c in self.alive_charas if c.action_points == max_action_points])

    def find_chara_by_source(self, source):
        for chara in self.charas:
            if chara.source is source:
                return chara


class BattleChara:
    def __init__(self, source, battle, team):
        self.battle = battle
        self.team = team

        self.source = source
        self.name = source.name
        self.element_type = source.element_type
        self.action_points = 0

        self.skill_settings = list(source.skill_settings.all().order_by('order').select_related('skill'))

        if isinstance(source, Chara):
            self.create_from_chara(source)
        elif isinstance(source, (Monster, WorldBoss)):
            self.create_from_monster(source)
        else:
            raise Exception("illegal source")

        self.speed = max(self.speed, 100)
        # 暴擊率
        # 奧義類型10:暴擊率提升
        self.critical = min(250, 20 + self.dex // 3)
        self.critical += self.ability_type_power(10) * 1000 * max(1, self.dex / 1000)

        self.eva_add = 0
        self.poison = 0
        self.blocked_ability_count = 0
        self.weapon_effect_blocked = False
        self.weapon_effect_blocked_flag = False
        self.reduced_skill_rate = 0

        # 奧義類型15:增加初始AP
        self.action_points += self.ability_type_power(15)

    def set_attributes(self):
        for attr in self.source.attributes.all().select_related('type'):
            attr_value = attr.value
            if isinstance(self.source, Monster):
                attr_value = int(attr_value * self.battle.difficulty)
            if isinstance(self.source, Chara):
                attr_value = int(attr_value * (1 + self.source.buff_effect_power(attr.type.id) / 100))

            if self.battle.element_type is not None:
                if self.element_type == self.battle.element_type and self.element_type.id != 'none':
                    attr_value = int(attr_value * (1.1 + self.ability_type_power(19)))
                elif self.element_type.suppressed_by_id == self.battle.element_type.id:
                    attr_value = int(attr_value * 0.9)
            setattr(self, attr.type.en_name, attr_value)

    def create_from_chara(self, chara):
        # 裝備
        self.equipments = {}
        for slot in chara.slots.all().select_related('item__equipment', 'item__type'):
            if slot.item:
                self.equipments[slot.type_id] = slot.item.equipment
            else:
                self.equipments[slot.type_id] = EmptyEquipment()

        # 奧義
        self.ability_types = chara.equipped_ability_types

        self.set_attributes()

        # 攻防
        # 奧義類型18:魔法劍
        self.attack = self.str + int(self.int * self.ability_type_power(18)) + \
            sum(x.attack for x in self.equipments.values()) + self.equipments[1].weight // 5
        self.defense = self.vit + sum(x.defense for x in self.equipments.values())
        self.magic_defense = (self.men + self.equipments[4].defense) // 2
        self.speed = self.agi - sum(x.weight for x in self.equipments.values())

        # hp, mp
        for field in ['hp', 'hp_max', 'mp', 'mp_max']:
            setattr(self, field, getattr(chara, field))

        if self.battle.battle_type == 'pvp':
            self.hp = self.hp_max
            self.mp = self.mp_max

        self.luck_sigmoid = chara.luck_sigmoid

        # 同屬武防提升HP
        equipmen_hp_bonus = 0.1 * \
            (int(self.equipments[1].element_type_id == self.element_type.id) +
             int(self.equipments[2].element_type_id == self.element_type.id))
        self.hp_max += int(self.hp_max * equipmen_hp_bonus)
        self.hp += int(self.hp * equipmen_hp_bonus)
        # 同屬飾品提升MP
        equipmen_mp_bonus = 0.1 * int(self.equipments[3].element_type_id == self.element_type.id)
        self.mp_max += int(self.mp_max * equipmen_mp_bonus)
        self.mp += int(self.mp * equipmen_mp_bonus)

    def create_from_monster(self, monster):
        abilities = list(monster.abilities.all())
        self.ability_types = {
            ability.type_id: ability
            for ability in sorted(abilities, key=lambda x: x.power)
        }

        self.set_attributes()

        # 奧義類型18:魔法劍
        self.attack = self.str + int(self.int * self.ability_type_power(18))
        self.defense = self.vit
        self.magic_defense = self.men // 2
        self.speed = self.agi

        if isinstance(self.source, WorldBoss):
            for field in ['hp', 'hp_max', 'mp', 'mp_max']:
                setattr(self, field, getattr(monster, field))
        else:
            self.hp = self.hp_max = int(monster.hp * self.battle.difficulty)
            self.mp = self.mp_max = int(monster.mp * self.battle.difficulty)

        self.luck_sigmoid = 0.5

    @property
    def profile(self):
        return {
            field: getattr(self, field) for field in ['team', 'name', 'action_points', 'hp_max', 'hp', 'mp_max', 'mp']
        }

    @property
    def hate(self):
        return 100 + self.ability_type_power(59)

    @property
    def alive_enemy_charas(self):
        return [chara for chara in self.battle.alive_charas if chara.team != self.team]

    def pick_alive_enemy_chara(self):
        charas = self.alive_enemy_charas
        return choices(charas, weights=[x.hate for x in charas])[0]

    def take_action(self):
        self.before_action()

        defender = self.pick_alive_enemy_chara()
        skill = self.get_skill(defender)

        if skill is None:
            self.normal_attack(defender)
        else:
            self.perform_skill(defender, skill)

        self.after_action()

    def log(self, message):
        self.battle.logs[-1]['actions'].append({'team': self.team, 'chara': self.name, 'message': message})

    def increase_action_points(self):
        # 奧義類型53:天使之翼
        self.action_points += int(self.speed * (1 + self.ability_type_power(53)))

    def get_skill(self, defender):
        for skill_setting in self.skill_settings:
            if self.hp / self.hp_max * 100 <= skill_setting.hp_percentage \
                    and self.mp / self.mp_max * 100 <= skill_setting.mp_percentage \
                    and defender.hp / defender.hp_max * 100 <= skill_setting.defender_hp_percentage \
                    and defender.mp / defender.mp_max * 100 <= skill_setting.defender_mp_percentage:
                break
        else:
            return None

        skill = skill_setting.skill
        rate = skill.rate
        mp_cost = skill.mp_cost
        # 奧義類型6:魔力之術
        if self.has_ability_type(6):
            mp_cost -= int(mp_cost * self.ability_type_power(6))
        # 無防
        if self.has_equipment_effect(2, 1):
            mp_cost -= int(mp_cost * 0.5)
            self.log(f"[無防特效]{self.name}的技能MP消耗降低")

        # 奧義類型25:戰技激發
        if self.has_ability_type(25):
            rate += rate // 2
        rate -= int(rate * self.reduced_skill_rate)

        if self.mp >= skill.mp_cost and rate >= randint(1, 100):
            self.mp -= mp_cost
            return skill
        else:
            return None

    def before_action(self):
        # 毒
        if self.poison > 0:
            hp_loss = min(self.hp - 1, int(self.hp_max * self.poison / 100))
            self.hp -= hp_loss
            self.log(f"{self.name}因中毒失去了{hp_loss}點 HP")

            if 20 + self.ability_type_power(42) >= randint(1, 100):
                self.poison = 0
                self.log(f"{self.name}成功解掉身上的毒")

        # 奧義類型1:再生
        if self.has_ability_type(1):
            hp_add = int(self.hp_max * self.ability_type_power(1))
            self.gain_hp(hp_add)
            self.log(f"{self.name}恢復了{hp_add}點 HP")

    def after_action(self):
        self.weapon_effect_blocked = self.weapon_effect_blocked_flag
        self.weapon_effect_blocked_flag = False

        self.reduced_skill_rate = 0

    def has_ability_type(self, type_id):
        return type_id in self.ability_types

    def ability_type_power(self, type_id):
        if type_id in self.ability_types:
            return self.ability_types[type_id].power
        return 0

    def has_equipment_effect(self, slot_type_id, element_type_id):
        if self.weapon_effect_blocked and slot_type_id == 1:
            return False
        return hasattr(self, 'equipments') and self.equipments[slot_type_id].element_type_id == element_type_id == self.element_type.id

    def gain_hp(self, hp_add):
        self.hp = min(self.hp_max, self.hp + hp_add)

    def gain_mp(self, mp_add):
        self.mp = min(self.mp_max, self.mp + mp_add)

    def normal_attack(self, defender):
        self.log(f"{self.name}使出了普通攻擊")
        self.action_points -= 1000

        attack = self.attack

        # 奧義類型47:覺醒
        attack += int(attack * self.ability_type_power(47) * self.battle.rounds)
        # 奧義類型50:霸氣
        attack += int(attack * self.ability_type_power(50) * self.battle.rounds)
        # 奧義類型2:神擊
        attack += int(attack * self.ability_type_power(2))

        # 星防
        if self.has_equipment_effect(2, 5):
            attack += int(attack * 0.25)
            self.log(f"[星防特效]{self.name}造成的普攻攻擊力上升")

        damage_max = max(0, attack - defender.defense // 2)
        damage = randint(int(damage_max * (0.2 + 0.2 * self.luck_sigmoid)), damage_max)

        # 奧義類型3:防禦術
        damage -= int(damage * defender.ability_type_power(3))
        # 暗防
        if defender.has_equipment_effect(2, 8):
            damage -= int(damage * 0.4)
            defender.log(f"[暗防特效]{defender.name}受到的普攻傷害減低")

        defender.take_damage(self, damage)

    def perform_skill(self, defender, skill):
        self.log(f"{self.name}使出了{skill.name}")
        self.action_points -= skill.action_cost
        damage = None

        # 特殊技能
        # 不造成 damage
        # 不受技能加減成影響
        if skill.type_id == 2:
            hp_add = skill.power + randint(0, self.men // 2)
            self.hp = min(self.hp_max, self.hp + hp_add)
            self.log(f"{self.name}的 HP 恢復了{hp_add}點")
        elif skill.type_id == 3:
            hp_add = self.hp_max // 10
            mp_add = self.mp_max // 10
            self.hp = min(self.hp_max, self.hp + hp_add)
            self.mp = min(self.mp_max, self.mp + mp_add)
            self.log(f"{self.name}的 HP 恢復了{hp_add}點， MP 恢復了{mp_add}點")
        elif skill.type_id == 4:
            attack_add = int(self.men * skill.power / 100)
            self.attack += attack_add
            self.log(f"{self.name}的攻擊力上升了{attack_add}點")
        elif skill.type_id == 5:
            defense_add = int(self.men * skill.power / 100)
            self.defense += defense_add
            self.log(f"{self.name}的防禦力上升了{defense_add}點")
        elif skill.type_id == 6:
            magic_defense_add = int(self.men * skill.power / 100)
            self.magic_defense += magic_defense_add
            self.log(f"{self.name}的魔法防禦力上升了{magic_defense_add}點")
        elif skill.type_id == 8:
            mp_draw = min(800, defender.mp, defender.mp_max // 5)
            defender.mp -= mp_draw
            self.mp = min(self.mp_max, self.mp + mp_draw)
            self.log(f"{defender.name}被吸取了{mp_draw}點 MP")
        elif skill.type_id == 9:
            hp_loss = min(defender.hp - 1, int(defender.hp / skill.power))
            defender.hp -= hp_loss
            self.log(f"{defender.name}失去了{hp_loss}點 HP")
        elif skill.type_id == 19:
            hp_loss = self.hp // 10
            mp_add = self.hp_max // 10
            self.hp -= hp_loss
            self.mp = min(self.mp_max, self.mp + mp_add)
            self.log(f"{self.name}失去{hp_loss}點 HP，獲得 {mp_add} 點MP")
        elif skill.type_id == 21:
            hp_loss = min(defender.hp - 1, randint(0, self.mp))
            defender.hp -= hp_loss
            self.mp = 0
            self.log(f"{defender.name}失去了{hp_loss}點 HP")
        elif skill.type_id == 23:
            hp_loss = min(defender.hp - 1, randint(0, self.men) + self.agi)
            self.hp = min(self.hp_max, self.hp + hp_loss)
            defender.hp -= hp_loss
            self.log(f"{defender.name}被吸取了{hp_loss}點 HP")
        elif skill.type_id == 24:
            mp_loss = min(defender.mp, randint(0, self.men) + self.agi)
            self.mp = min(self.mp_max, self.mp + mp_loss)
            defender.mp -= mp_loss
            self.log(f"{defender.name}被吸取了{mp_loss}點 MP")
        elif skill.type_id == 25:
            mp_loss = min(defender.mp, self.int // 2 + randint(0, self.men * 2))
            defender.mp -= mp_loss
            self.log(f"{defender.name}失去了{mp_loss}點 MP")
        # 特殊技能結束

        # 一般技能
        # 造成 damage
        # 受技能加減成影響
        elif skill.type_id == 16:
            damage = skill.power * (randint(0, self.str) + self.int) - defender.magic_defense
        elif skill.type_id == 17:
            damage = skill.power + (randint(0, self.men) + self.int) - defender.magic_defense
        elif skill.type_id == 18:
            damage = skill.power * (self.int + randint(0, self.men) + randint(0, self.dex)) - defender.magic_defense
        elif skill.type_id == 20:
            damage = self.dex + randint(0, self.dex * skill.power)
        elif skill.type_id == 22:
            damage = self.vit + randint(0, self.dex * skill.power)
        elif skill.type_id in [1, 7, 10, 11, 12, 13, 14, 15]:
            damage = skill.power + randint(0, self.int) - defender.magic_defense
        elif skill.type_id == 26:
            damage = skill.power * (randint(0, self.int) + defender.defense)
        elif skill.type_id == 27:
            damage = skill.power * (randint(0, self.int) + defender.magic_defense)
        elif skill.type_id == 28:
            damage = skill.power * (randint(0, self.int) + defender.speed)

        # 一般技能結束

        if damage is None:
            return

        # 奧義類型51:魔神爆發
        if self.has_ability_type(51) and skill.type_id in [17, 18]:
            damage *= 2

        damage += int((self.int + self.men) * max(1000, skill.power) / 4000)

        # 奧義類型5:戰技
        damage += int(damage * self.ability_type_power(5))
        # 奧義類型7:戰防
        damage -= int(damage * defender.ability_type_power(7))
        # 無武
        if self.has_equipment_effect(1, 1):
            damage += int(damage * 0.4)
            self.log(f"[無武特效]{self.name}的技能傷害增加")

        # 光武
        if defender.has_equipment_effect(1, 7):
            damage -= int(damage * 0.3)
            defender.log(f"[光武特效]{defender.name}受到的技能傷害減少")
        # 光防
        if defender.has_equipment_effect(2, 7):
            damage -= int(damage * 0.64)
            defender.log(f"[光防特效]{defender.name}受到的技能傷害減少")

        defender.take_damage(self, damage, skill)

    def take_damage(self, attacker, damage, skill=None):
        skill_type = skill.type_id if skill is not None else None
        speed_gap = min(400, self.speed - attacker.speed)
        eva = min(400, (self.dex - attacker.dex // 2) // 3) + self.eva_add

        speed_gap_check = 1000
        eva_check = 1000
        # 奧義類型56:命中祝福
        if attacker.has_ability_type(56):
            speed_gap_check = 2000
            eva_check = 2000
        # 星武
        if attacker.has_equipment_effect(1, 5):
            speed_gap_check *= 10
            eva_check *= 10
            attacker.log(f"[星武特效]{attacker.name}的命中率上升")

        # 17,18,26無視反擊、迴避、躲避、奧義類型8
        if skill is not None and skill.type_id in [17, 18, 26]:
            pass
        # 奧義類型12:反擊
        elif self.has_ability_type(12) and randint(1, max(500, 1200 - self.men)) <= 100 * max(1, self.men / 1000):
            if attacker.ability_type_power(43) >= randint(1, 100):
                damage = None
                self.log(f"{self.name}的反擊發動！但被{attacker.name}回避了")
            else:
                hp_loss = int((damage + randint(0, self.str)) / 2 * self.ability_type_power(12) / 100)
                hp_loss = min(attacker.hp - 1, hp_loss)
                attacker.hp -= hp_loss
                damage = None
                self.log(f"{self.name}的反擊發動！對{attacker.name}造成了{hp_loss}點傷害")
        # 迴避
        elif eva >= randint(1, eva_check):
            damage = None
            self.log(f"{self.name}迴避了攻擊")
        # 躲避
        elif speed_gap >= randint(1, speed_gap_check):
            damage = None
            self.log(f"{self.name}躲避了攻擊")
        # 奧義類型8:神聖護體
        elif self.ability_type_power(8) >= randint(1, 100):
            damage = None
            self.log(f"{self.name}擋住了攻擊")

        # 未受到攻擊，不進入傷害與特效處理
        if damage is None:
            return

        # 暴擊處理
        # 奧義類型58:詛咒
        # 奧義類型44:安撫
        if attacker.critical * (1 - self.ability_type_power(58)) >= randint(1, 1000) and not self.has_ability_type(44):
            damage = int(damage * 1.5)
            # 奧義類型23:暴擊傷害提升
            damage += int(damage * attacker.ability_type_power(23))
            self.log(f"暴擊！")
        # 奧義類型26:追加傷害
        if attacker.has_ability_type(26) and randint(1, 3) == 1:
            damage_add = randint(0, 200)
            damage += damage_add
            attacker.log(f"追加了{damage_add}點傷害")
        # 屬性相剋
        if attacker.element_type == self.element_type.suppressed_by:
            damage = int(damage * 1.2)
            attacker.log(f"{self.name}的屬性被剋制了")

        damage = max(1, damage)
        self.hp = max(0, self.hp - damage)
        self.log(f"{self.name}受到了{damage}點傷害")

        # 奧義類型4:連擊
        attacker.action_points += int(attacker.ability_type_power(4))

        # 即死
        # 奧義類型9:即死
        if skill_type == 10 and randint(1, 30) == 1 or attacker.ability_type_power(9) >= randint(1, 1000):
            if self.battle.battle_type == 'dungeon' or isinstance(self.source, WorldBoss):
                self.log(f"因為神祕力量，即死被無效化了")
            # 奧義類型40:免疫即死
            elif self.ability_type_power(40) >= randint(1, 100):
                self.log(f"不死鳥保護住{self.name}")
            elif self.has_ability_type(49):
                if self.ability_type_power(49) >= randint(1, 100):
                    attacker.hp = 0
                    self.log(f"{attacker.name}對死神使出即死，但死神將即死回報給對方")
                else:
                    self.log(f"死神保護住{self.name}")
            else:
                self.hp = 0
                self.log(f"{self.name}即死")

        # 降防
        if skill_type == 11:
            self.defense -= self.defense // 10
            self.log(f"{self.name}的防禦力下降")

        # 毒
        # 奧義類型14:毒
        if skill_type == 12 and randint(1, 4) == 1 or attacker.has_ability_type(14) and randint(1, 6) == 1:
            self.poison = max(1, attacker.ability_type_power(14))
            self.log(f"{self.name}中毒了")

        # 攻擊者迴避提升
        if skill_type == 13 and randint(1, 3) == 1 and attacker.eva_add < 600:
            attacker.eva_add += 40
            attacker.log(f"{attacker.name}的迴避提升了")

        # 麻痹
        # 奧義類型24:麻痹
        if skill_type == 14 and randint(1, 8) == 1 or attacker.has_ability_type(24) and randint(1, 15) == 1:
            self.action_points -= 2000
            self.log(f"{self.name}被麻痹了")

        # 吸血
        # 奧義類型28:吸血
        if skill_type == 7 or attacker.has_ability_type(28) and randint(1, 4) == 1:
            hp_add = damage // 2
            attacker.hp = min(attacker.hp_max, attacker.hp + hp_add)
            self.log(f"{self.name}被吸取了{hp_add}點 HP")

        # 降速
        # 奧義類型16:降速
        if skill_type == 15 and randint(1, 8) or attacker.ability_type_power(16) >= randint(1, 100):
            self.speed = max(0, self.speed - 50)
            self.log(f"{self.name}的速度降低了")

        # 奧義類型27:嗜魔
        if attacker.has_ability_type(27) and randint(1, 3) == 1:
            mp_loss = min(self.mp, randint(0, 150))
            self.mp -= mp_loss
            attacker.mp = min(attacker.mp_max, attacker.mp + mp_loss)
            self.log(f"{self.name}的MP被奪走了")

        # 奧義類型45:束縛
        if attacker.has_ability_type(45):
            self.action_points -= attacker.ability_type_power(45)
            self.log(f"[束縛]{self.name}的AP減少了")

        # 奧義類型54:亡命鎖鏈
        if attacker.has_ability_type(54):
            hp_loss = int(attacker.hp_max * attacker.ability_type_power(54))
            attacker.hp = max(0, attacker.hp - hp_loss)
            self.hp = max(0, self.hp - hp_loss * 2)
            attacker.log(f"[亡命鎖鏈]{attacker.name}自身扣血{hp_loss}")
            self.log(f"[亡命鎖鏈]{self.name}扣血{hp_loss*2}")

        # 奧義類型55:吸血鬼之吻
        if attacker.has_ability_type(55) and randint(1, 7) == 1:
            hp_loss = min(self.hp, int((attacker.hp_max - attacker.hp) / attacker.ability_type_power(55)) +
                          randint(1, attacker.agi + attacker.dex))
            mp_loss = min(self.mp, int((attacker.mp_max - attacker.mp) / attacker.ability_type_power(55)) +
                          randint(1, attacker.agi + attacker.dex))
            self.hp -= hp_loss
            self.mp -= mp_loss
            attacker.gain_hp(hp_loss)
            attacker.gain_mp(mp_loss)
            attacker.log(f"[吸血鬼之吻]吸收了{self.name}的{hp_loss}HP與{mp_loss}MP")

        # 奧義類型31:封印
        # 奧義類型52:十字封印
        if (attacker.has_ability_type(31) or attacker.has_ability_type(52)) and randint(1, 5 * 2 ** self.blocked_ability_count) == 1:
            # 奧義類型57:神之封印
            if self.blocked_ability_count >= max(attacker.ability_type_power(31), attacker.ability_type_power(52)) + attacker.ability_type_power(57):
                pass
            # 奧義類型41:封印防護
            elif not attacker.has_ability_type(52) and self.ability_type_power(41) >= randint(1, 100):
                self.log(f"封印{self.name}的奧義失敗")
            elif len(self.ability_types) > 0:
                ability = self.ability_types.pop(choice(list(self.ability_types.keys())))
                self.blocked_ability_count += 1
                self.log(f"{self.name}的{ability.name}被封印了")

        # 火武
        if attacker.has_equipment_effect(1, 2):
            hp_loss = int(min(self.hp_max, attacker.hp_max * 15) * 0.01)
            self.hp -= hp_loss
            self.log(f"[火武特效]{self.name}損失了{hp_loss}HP")
        # 水武
        elif attacker.has_equipment_effect(1, 3):
            hp_loss = int(min(self.hp_max, attacker.hp_max * 15) * 0.005)
            self.hp -= hp_loss
            attacker.gain_hp(hp_loss)
            attacker.log(f"[水武特效]吸收了{self.name}的{hp_loss}HP")
        # 風武
        elif attacker.has_equipment_effect(1, 4):
            ap_add = min(max(100, self.speed // 10), 500)
            attacker.action_points += ap_add
            attacker.log(f"[風武特效]{attacker.name}獲得了{ap_add}AP")
        # 雷武
        elif attacker.has_equipment_effect(1, 6):
            if randint(1, 5) == 1:
                self.action_points -= 1000
                self.log(f"[雷武特效]{self.name}被麻痹了，減少了1000AP")
        # 暗武
        elif attacker.has_equipment_effect(1, 8):
            self.reduced_skill_rate = 0.5
            self.log(f"[暗武特效]{self.name}的技能發動率被降低了")

        if self.hp <= 0:
            pass
        # 火防
        elif self.has_equipment_effect(2, 2):
            hp_loss = int(min(attacker.hp_max, self.hp_max * 15) * 0.015)
            attacker.hp -= hp_loss
            attacker.log(f"[火防特效]{attacker.name}損失了{hp_loss}HP")
        # 水防
        elif self.has_equipment_effect(2, 3):
            hp_add = int(self.hp_max * 0.005)
            self.gain_hp(hp_add)
            attacker.weapon_effect_blocked_flag = True
            self.log(f"[水防特效]{self.name}恢復了{hp_add}HP，並封印了對手的武器特效")
        # 風防
        elif self.has_equipment_effect(2, 4):
            ap_add = max(100, attacker.speed // 10)
            self.action_points += ap_add
            self.log(f"[風防特效]{self.name}獲得了{ap_add}AP")
        # 雷防
        elif self.has_equipment_effect(2, 6):
            ap_loss = max(100, attacker.speed // 10)
            attacker.action_points -= ap_loss
            attacker.log(f"[雷防特效]{attacker.name}的AP減少了{ap_loss}點")

        for chara in [self, attacker]:
            if chara.hp <= 0:
                chara.hp = 0
                chara.log(f"{chara.name}倒下了")

                # 奧義類型11:復活
                if chara.ability_type_power(11) >= randint(1, 100):
                    chara.hp = chara.hp_max // 2
                    chara.log(f"{chara.name}復活了")
