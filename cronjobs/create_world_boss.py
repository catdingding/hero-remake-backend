import sys
import django

sys.path.insert(0, "/app")
django.setup()

import random
from datetime import timedelta
from django.utils.timezone import localtime
from django.db import transaction
from django.db.models import Q
from ability.models import Ability
from battle.models import WorldBossTemplate, WorldBoss, WorldBossAttribute, WorldBossSkillSetting, WorldBossNameBase
from world.models import ElementType, AttributeType, Location
from system.utils import push_log


def generate_name():
    names_1 = WorldBossNameBase.objects.filter(category='1').values_list('name', flat=True)
    names_2 = WorldBossNameBase.objects.filter(category='2').values_list('name', flat=True)

    return random.choice(names_1) + '之' + random.choice(names_2)


for template in WorldBossTemplate.objects.all():
    prev_instance = WorldBoss.objects.filter(template=template).order_by('-created_at').first()
    if prev_instance and prev_instance.is_alive:
        if (localtime() - prev_instance.created_at) > timedelta(hours=18):
            WorldBoss.objects.filter(id=prev_instance.id).update(is_alive=False)
            push_log("神獸", f"{prev_instance.name}消失了……")
            template.difficulty /= 1.1
        else:
            continue
    elif prev_instance and (prev_instance.updated_at - prev_instance.created_at) < timedelta(hours=6):
        template.difficulty *= 1.1
    elif prev_instance and (prev_instance.updated_at - prev_instance.created_at) > timedelta(hours=12):
        template.difficulty /= 1.1

    if template.difficulty < 0.1:
        template.difficulty = 0.1

    with transaction.atomic():
        name = generate_name()
        element_type = random.choice(ElementType.objects.all())
        world_boss = WorldBoss.objects.create(
            template=template, name=name, element_type=element_type, location=Location.objects.get(x=0, y=0),
            hp=int(template.base_hp * template.difficulty), hp_max=int(template.base_hp * template.difficulty),
            mp=int(template.base_mp * template.difficulty), mp_max=int(template.base_mp * template.difficulty)
        )

        WorldBossAttribute.objects.bulk_create([
            WorldBossAttribute(world_boss=world_boss, type=x, value=template.base_attribute * template.difficulty)
            for x in AttributeType.objects.all()
        ])

        WorldBossSkillSetting.objects.create(
            world_boss=world_boss, skill_id=random.choice([198, 199, 200]),
            hp_percentage=100, mp_percentage=100, order=0
        )

        world_boss.abilities.add(92, 93)
        world_boss.abilities.add(*random.choices(Ability.objects.filter(~Q(id__in=[92, 93])), k=8))

        template.save()

        push_log("神獸", f"{name}於(0,0)生成了")
