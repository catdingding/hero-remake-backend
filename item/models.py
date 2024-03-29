from random import choices
from collections import Counter

from django.db import models
from base.models import BaseModel


class ItemUseEffect(BaseModel):
    name = models.CharField(max_length=10, unique=True)


class ItemCategory(BaseModel):
    name = models.CharField(max_length=10, unique=True)


class ItemType(BaseModel):
    name = models.CharField(max_length=30, unique=True)

    category = models.ForeignKey("item.ItemCategory", on_delete=models.PROTECT)
    element_type = models.ForeignKey("world.ElementType", null=True, on_delete=models.PROTECT)
    attribute_type = models.ForeignKey("world.AttributeType", null=True, on_delete=models.PROTECT)
    slot_type = models.ForeignKey("world.SlotType", null=True, on_delete=models.PROTECT)

    use_effect = models.ForeignKey("item.ItemUseEffect", null=True, on_delete=models.PROTECT)
    use_effect_param = models.IntegerField(null=True)
    # if True, disappear after use
    is_consumable = models.BooleanField(default=False)
    is_transferable = models.BooleanField(default=True)

    value = models.IntegerField(default=0)

    power = models.IntegerField(default=0)
    attack = models.IntegerField(default=0)
    defense = models.IntegerField(default=0)
    weight = models.IntegerField(default=0)

    ability_1 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_1_itemtypes", on_delete=models.PROTECT)
    ability_2 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_2_itemtypes", on_delete=models.PROTECT)

    description = models.CharField(max_length=100)

    def make(self, number):
        # equipment
        if self.category_id == 1:
            return [
                Equipment.objects.create(
                    type=self, number=1, quality=choices(['普通', '優良', '稀有'], weights=[20, 2, 1])[0],
                    element_type=self.element_type, custom_name=self.name,
                    ability_1_id=self.ability_1_id, ability_2_id=self.ability_2_id
                ).item_ptr
                for i in range(number)
            ]

        # others
        else:
            return [Item(type=self, number=number)]


class PetType(BaseModel):
    item_type = models.OneToOneField("item.ItemType", related_name="pet_type", on_delete=models.PROTECT)

    upgrade_proficiency_cost = models.IntegerField()

    attack_growth = models.IntegerField()
    defense_growth = models.IntegerField()
    weight_growth = models.IntegerField()


class PetTypeEvolutionTarget(BaseModel):
    pet_type = models.ForeignKey("item.PetType", related_name="evolution_targets", on_delete=models.PROTECT)
    target_pet_type = models.ForeignKey("item.PetType", on_delete=models.PROTECT)
    weight = models.IntegerField()


class Item(BaseModel):
    id = models.BigAutoField(primary_key=True)
    type = models.ForeignKey("item.ItemType", on_delete=models.PROTECT)
    number = models.PositiveIntegerField()

    @property
    def name(self):
        return self.equipment.display_name if self.type.category_id == 1 else self.type.name


class Equipment(Item):
    QUALITY_CHOICES = [(x, x) for x in ['稀有', '優良', '普通']]
    QUALITY_UPGRADE_TIMES_LIMIT = {
        '普通': 50,
        '優良': 60,
        '稀有': 70
    }

    quality = models.CharField(max_length=2, choices=QUALITY_CHOICES)

    custom_name = models.CharField(max_length=20)

    element_type = models.ForeignKey("world.ElementType", on_delete=models.PROTECT)

    attack_base = models.IntegerField(default=0)
    defense_base = models.IntegerField(default=0)
    weight_base = models.IntegerField(default=0)

    attack_add_on = models.IntegerField(default=0)
    defense_add_on = models.IntegerField(default=0)
    weight_add_on = models.IntegerField(default=0)

    upgrade_times = models.IntegerField(default=0)

    ability_1 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_1_items", on_delete=models.PROTECT)
    ability_2 = models.ForeignKey("ability.Ability", null=True,
                                  related_name="ability_2_items", on_delete=models.PROTECT)

    battle_effect = models.ForeignKey("battle.BattleEffect", null=True, on_delete=models.PROTECT)

    is_locked = models.BooleanField(default=False)

    @property
    def attack(self):
        return self.type.attack + self.attack_base + self.attack_add_on

    @property
    def defense(self):
        return self.type.defense + self.defense_base + self.defense_add_on

    @property
    def weight(self):
        return self.type.weight + self.weight_base + self.weight_add_on

    @property
    def upgrade_times_limit(self):
        if self.type.slot_type_id in [1, 2, 3]:
            return self.QUALITY_UPGRADE_TIMES_LIMIT[self.quality]
        else:
            return 10

    @property
    def display_name(self):
        if self.quality == '普通':
            return f"{self.custom_name}"
        else:
            return f"{self.quality}的{self.custom_name}"


class ItemTypePoolGroup(BaseModel):
    name = models.CharField(max_length=20, unique=True)

    def pick(self, n=1):
        assert n >= 0
        if n == 0:
            return []

        members = self.members.all()
        picked_members = choices(members, weights=[m.weight for m in members], k=n)
        picked_pools = [x.pool_id for x in picked_members]

        items = []
        for pool_id, count in Counter(picked_pools).items():
            items.extend(ItemTypePool.objects.get(id=pool_id).pick(count))

        return items


class ItemTypePoolGroupMember(BaseModel):
    group = models.ForeignKey("item.ItemTypePoolGroup", on_delete=models.CASCADE, related_name="members")

    pool = models.ForeignKey("item.ItemTypePool", on_delete=models.CASCADE)
    weight = models.PositiveIntegerField(default=10000)


class ItemTypePool(BaseModel):
    name = models.CharField(max_length=20, unique=True)

    def pick(self, n=1):
        assert n >= 0
        if n == 0:
            return []

        members = self.members.all()
        picked_members = choices(members, weights=[m.weight for m in members], k=n)
        picked_item_types = [x.item_type_id for x in picked_members]

        items = []
        for item_type_id, count in Counter(picked_item_types).items():
            items.extend(ItemType.objects.get(id=item_type_id).make(count))

        return items


class ItemTypePoolMember(BaseModel):
    pool = models.ForeignKey("item.ItemTypePool", on_delete=models.CASCADE, related_name="members")

    item_type = models.ForeignKey("item.ItemType", on_delete=models.CASCADE)
    number = models.PositiveIntegerField(default=1)
    weight = models.PositiveIntegerField(default=10000)
