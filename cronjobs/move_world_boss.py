import sys
import django

sys.path.insert(0, "/app")
django.setup()

import random

from battle.models import WorldBoss
from world.models import Location
from system.utils import push_log


for world_boss in WorldBoss.objects.filter(is_alive=True):
    location = random.choice(Location.objects.all())
    WorldBoss.objects.filter(id=world_boss.id).update(location=location)

    push_log("神獸", f"{world_boss.name}移動到了({location.x},{location.y})")
