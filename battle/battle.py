from random import choice

from base.utils import randint
from battle.models import Monster
from chara.models import Chara
from item.models import Equipment

class Battle:
    def __init__(self, attackers, defenders):
        self.charas = [BattleChara(x, battle=self, team='attacker') for x in attackers] + \
            [BattleChara(x, battle=self, team='defender') for x in defenders]

        self.executed = False
        self.logs = []
        self.rounds = 0

    @property
    def max_rounds(self):
        return 400

    @property
    def winner(self):
        if not any(chara.team == 'attacker' for chara in self.alive_charas):
            return "defenders"
        elif not any(chara.team == 'defender' for chara in self.alive_charas):
            return "attackers"
        else:
            return "draw"

    def execute(self):
        assert not self.executed
        self.executed = True

        while True:
            self.logs.append({'actions': []})

            act_chara = self.get_act_chara()
            if act_chara is None:
                self.next_round()
            else:
                act_chara.take_action()

            self.logs[-1]['charas'] = [chara.profile for chara in self.charas]
            if self.winner != 'draw' or self.rounds >= self.max_rounds:
                break

    @property
    def alive_charas(self):
        return [chara for chara in self.charas if chara.hp > 0]

    def next_round(self):
        self.rounds += 1

        for chara in self.alive_charas:
            chara.action_points += chara.speed

    def get_act_chara(self):
        max_action_points = max([c.action_points for c in self.alive_charas])
        if max_action_points < 1000:
            return None
        else:
            return choice([c for c in self.charas if c.action_points == max_action_points])


class BattleChara:
    def __init__(self, source, battle, team):
        self.battle = battle
        self.team = team

        self.name = source.name
        self.action_points = 0
        for attr in source.attributes.all():
            setattr(self, attr.type_id, attr.value)
        self.skill_settings = list(source.skill_settings.all().order_by('order').select_related('skill'))

        if isinstance(source, Chara):
            self.create_from_chara(source)
        elif isinstance(source, Monster):
            self.create_from_monster(source)
        else:
            raise Exception("illegal source")

        # 閃避
        self.eva = min(400, self.dex // 3) + self.ability_type_power(8) * 10
        # 暴擊
        self.critical = min(250, 20 + self.dex // 3 + self.ability_type_power(10) * 10)

        self.poison = 0
        self.blocked_ability_count = 0

    def create_from_chara(self, chara):
        # 裝備
        self.equipments = {}
        for slot in chara.slots.all().select_related('item__equipment'):
            if slot.item:
                self.equipments[slot.type_id] = slot.item.equipment
            else:
                self.equipments[slot.type_id] = Equipment()

        # 奧義
        abilities = []
        for equipment in self.equipments.values():
            abilities.append(equipment.ability_1)
            abilities.append(equipment.ability_2)
        abilities.append(chara.main_ability)
        abilities.append(chara.job_ability)
        abilities = list(filter(None, abilities))
        self.ability_type = {
            ability.type_id: ability
            for ability in sorted(abilities, key=lambda x: x.power)
        }

        # 攻防
        self.attack = self.str + int(self.int * self.ability_type_power(8) / 100) + \
            sum(x.attack for x in self.equipments.values()) + self.equipments['weapon'].weight // 5
        self.defense = self.vit + sum(x.defense for x in self.equipments.values())
        self.magic_defense = (self.men + self.equipments['pet'].defense) // 2
        self.speed = self.agi - sum(x.weight for x in self.equipments.values())

        # hp, mp
        for field in ['hp', 'hp_max', 'mp', 'mp_max']:
            setattr(self, field, getattr(chara, field))

    def create_from_monster(self, monster):
        abilities = list(monster.abilities.all())
        self.ability_type = {
            ability.type_id: ability
            for ability in sorted(abilities, key=lambda x: x.power)
        }

        self.attack = self.str + int(self.int * self.ability_type_power(8) / 100)
        self.defense = self.vit
        self.magic_defense = self.men // 2
        self.speed = self.agi

        self.hp = self.hp_max = monster.hp
        self.mp = self.mp_max = monster.mp

    @property
    def profile(self):
        return {
            field: getattr(self, field) for field in ['team', 'name', 'action_points', 'hp_max', 'hp', 'mp_max', 'mp']
        }

    @property
    def alive_enemy_charas(self):
        return [chara for chara in self.battle.alive_charas if chara.team != self.team]

    def get_alive_enemy_chara(self):
        return choice(self.alive_enemy_charas)

    def take_action(self):
        self.before_action()

        skill = self.get_skill()
        defender = self.get_alive_enemy_chara()

        if skill is None:
            self.normal_attack(defender)
        else:
            self.perform_skill(defender, skill)

        self.after_action()

    def log(self, message):
        self.battle.logs[-1]['actions'].append({'chara': self.name, 'message': message})

    def get_skill(self):
        for skill_setting in self.skill_settings:
            if self.hp / self.hp_max <= skill_setting.hp_percentage \
                    and self.mp / self.mp_max <= skill_setting.mp_percentage:
                break
        else:
            return None

        skill = skill_setting.skill
        rate = skill.rate
        mp_cost = skill.mp_cost
        # 魔力之術
        if self.has_ability_type(6):
            mp_cost -= int(mp_cost * self.ability_type[6].power / 100)
        # 戰技激發
        if self.has_ability_type(25):
            rate += rate // 2

        if self.mp >= skill.mp_cost and skill.rate >= randint(1, 100):
            self.mp -= mp_cost
            return skill
        else:
            return None

    def before_action(self):
        if self.poison > 0:
            hp_loss = min(self.hp - 1, int(self.hp_max * self.poison / 100))
            self.hp -= hp_loss
            self.log(f"因中毒失去了{hp_loss}點 HP")

            if 20 + self.ability_type_power(42) >= randint(1, 100):
                self.log(f"成功解掉身上的毒")

        if self.has_ability_type(1):
            hp_add = int(self.hp_max * self.ability_type_power(1) / 100)
            self.gain_hp(hp_add)
            self.log(f"恢復了{hp_add}點 HP")

    def after_action(self):
        pass

    def has_ability_type(self, type_id):
        return type_id in self.ability_type

    def ability_type_power(self, type_id):
        try:
            return self.ability_type[type_id].power
        except KeyError:
            return 0

    def gain_hp(self, hp_add):
        self.hp = min(self.hp_max, self.hp + hp_add)

    def gain_mp(self, mp_add):
        self.mp = min(self.mp_max, self.mp + mp_add)

    def normal_attack(self, defender):
        self.log(f"{self.name}使出了普通攻擊")
        self.action_points -= 1000
        damage = randint(0, max(0, self.attack - defender.defense // 2))

        # 覺醒
        damage += int(damage * self.ability_type_power(47) * self.battle.rounds / 100)
        # 霸氣
        damage += int(damage * self.ability_type_power(50) * self.battle.rounds / 100)
        # 神擊系
        damage += int(damage * self.ability_type_power(2) / 100)
        # 防禦術
        damage -= int(damage * defender.ability_type_power(3) / 100)

        defender.take_damage(self, damage)

    def perform_skill(self, defender, skill):
        self.log(f"{self.name}使出了{skill.name}")
        self.action_points -= skill.action_cost
        damage = None

        # 特殊技能
        # 不造成 damage
        # 不可反擊/迴避
        # 不受技能加減成影響
        if skill.type_id == 2:
            hp_add = skill.power + randint(0, self.men // 2)
            self.hp = min(self.hp_max, self.hp + hp_add)
            self.log(f"HP 恢復了{hp_add}點")
        elif skill.type_id == 3:
            hp_add = self.hp_max // 10
            mp_add = self.mp_max // 10
            self.hp = min(self.hp_max, self.hp + hp_add)
            self.mp = min(self.mp_max, self.mp + mp_add)
            self.log(f"HP 恢復了{hp_add}點， MP 恢復了{mp_add}點")
        elif skill.type_id == 4:
            attack_add = int(self.men * skill.power / 100)
            self.attack += attack_add
            self.log(f"攻擊力上升了{attack_add}點")
        elif skill.type_id == 5:
            defense_add = int(self.men * skill.power / 100)
            self.defense += defense_add
            self.log(f"防禦力上升了{defense_add}點")
        elif skill.type_id == 6:
            magic_defense_add = int(self.men * skill.power / 100)
            self.magic_defense += magic_defense_add
            self.log(f"魔法防禦力上升了{magic_defense_add}點")
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
            mp_add = self.mp_max // 10
            self.hp -= hp_loss
            self.mp = min(self.mp_max, self.mp + mp_add)
            self.log(f"失去{hp_loss}點 HP，獲得 {mp_add} 點MP")
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
        # 可以反擊/迴避
        # 受技能加減成影響
        elif skill.type_id == 7:
            damage = skill.power + randint(0, self.int) - defender.magic_defense
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
        elif skill.type_id in [1, 10, 11, 12, 13, 14, 15]:
            damage = skill.power + randint(0, self.int) - defender.magic_defense
        # 一般技能結束

        if damage is None:
            return

        # 魔神爆發
        if self.has_ability_type(51) and skill.type_id in [17, 18]:
            damage *= 2

        damage += int((self.int + self.men) * max(1000, skill.power) / 4000)

        # 戰技
        damage += int(damage * self.ability_type_power(5) / 100)
        # 戰防
        damage -= int(damage * defender.ability_type_power(7) / 100)

        defender.take_damage(self, damage, skill)

    def take_damage(self, attacker, damage, skill=None):
        skill_type = skill.type_id if skill is not None else None
        speed_gap = min(400, self.speed - attacker.speed)

        speed_gap_check = 1000
        eva_check = 1000
        # 命中祝福
        if attacker.has_ability_type(56):
            speed_gap_check = 2000
            eva_check = 2000

        # 反擊
        if self.has_ability_type(12) and randint(1, max(500, 1200 - self.men)) <= 100:
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
        elif self.eva >= randint(1, eva_check):
            damage = None
            self.log(f"{self.name}迴避了攻擊")
        # 躲避
        elif speed_gap >= randint(1, speed_gap_check):
            damage = None
            self.log(f"{self.name}躲避了攻擊")
        # 神聖護體
        elif self.ability_type_power(8) >= randint(1, 100):
            damage = None
            self.log(f"{self.name}擋住了攻擊")

        # 未受到攻擊，不進入傷害與特效處理
        if damage is None:
            return

        # 暴擊
        if attacker.critical >= randint(1, 1000) and not self.has_ability_type(44):
            damage = int(damage * 1.5)
            damage += int(damage * attacker.ability_type_power(23) / 100)
            self.log(f"暴擊！")
        # 追加傷害
        if attacker.has_ability_type(26) and randint(1, 3) == 1:
            damage_add = randint(0, 200)
            damage += damage_add
            attacker.log(f"追加了{damage_add}點傷害")

        damage = max(1, damage)
        self.hp = max(0, self.hp - damage)
        self.log(f"{self.name}受到了{damage}點傷害")

        # 即死
        if skill_type == 10 and randint(1, 30) == 1 or attacker.ability_type_power(9) >= randint(1, 1000):
            if self.ability_type_power(40) >= randint(1, 100):
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
        if skill_type == 12 and randint(1, 4) == 1 or attacker.has_ability_type(14) and randint(1, 6) == 1:
            self.poison = max(1, attacker.ability_type_power(14))
            self.log(f"{self.name}中毒了")

        # 攻擊者迴避提升
        if skill_type == 13 and randint(1, 3) == 1 and attacker.eva < 1000:
            attacker.eva += 40
            attacker.log(f"{attacker.name}的迴避提升了")

        # 麻痹
        if skill_type == 14 and randint(1, 8) == 1 or attacker.has_ability_type(24) and randint(1, 15) == 1:
            self.action_points -= 2000
            self.log(f"{self.name}被麻痹了")

        # 吸血
        if skill_type == 7 or attacker.has_ability_type(28) and randint(1, 4) == 1:
            hp_add = damage // 2
            attacker.hp = min(attacker.hp_max, attacker.hp + hp_add)
            self.log(f"{self.name}被吸取了{hp_add}點 HP")

        # 降速
        if skill_type == 15 and randint(1, 8) or attacker.ability_type_power(16) >= randint(1, 1000):
            self.speed = max(0, self.speed - 50)
            self.log(f"{self.name}的速度降低了")

        # 嗜魔
        if attacker.has_ability_type(27) and randint(1, 3) == 1:
            mp_loss = min(self.mp, randint(0, 150))
            self.mp -= mp_loss
            attacker.mp = min(attacker.mp_max, attacker.mp + mp_loss)
            self.log(f"{self.name}的MP被奪走了")

        # 封印
        if attacker.has_ability_type(31) and randint(1, 10 * 2 ** self.blocked_ability_count) == 1:
            if self.ability_type_power(41) >= randint(1, 100):
                self.log(f"封印{self.name}的奧義失敗")
            elif len(self.ability_type) > 0:
                ability = self.ability_type.pop(choice(list(self.ability_type.keys())))
                self.blocked_ability_count += 1
                self.log(f"{self.name}的{ability.name}被封印了")

        if self.hp == 0:
            self.log(f"{self.name}倒下了")

            if self.ability_type_power(11) >= randint(1, 100):
                self.hp = self.hp_max // 2
                self.log(f"{self.name}復活了")
