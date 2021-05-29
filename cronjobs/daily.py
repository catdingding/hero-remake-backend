import sys
import django

sys.path.insert(0, "/app")
django.setup()

from chara.models import CharaRecord

CharaRecord.objects.update(today_battle=0)
