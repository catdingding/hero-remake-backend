import sys
import django
from datetime import datetime, timedelta

sys.path.insert(0, "/app")
django.setup()

from battle.models import BattleResult

BattleResult.objects.filter(created_at__lt=datetime.now()-timedelta(hours=1)).delete()
