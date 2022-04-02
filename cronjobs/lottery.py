from random import randint
import sys
import django
from django.db.models import F

sys.path.insert(0, "/app")
django.setup()

from chara.models import Chara
from trade.models import Lottery

from chara.achievement import update_achievement_counter
from system.utils import push_log


for lottery in Lottery.objects.all():
    number = randint(lottery.number_min, lottery.number_max)
    tickets = lottery.tickets.filter(nth=lottery.nth, number=number)
    gold = lottery.gold

    if tickets:
        gold_per_ticket = gold // len(tickets)
        for ticket in tickets:
            Chara.objects.filter(id=ticket.chara_id).update(gold=F('gold') + gold_per_ticket)
            update_achievement_counter(ticket.chara, 18, 1, 'increase')
        gold = 0
        message = f"恭喜{'、'.join(x.chara.name for x in tickets)}中獎，平分{lottery.gold}獎金！"
    else:
        message = "無人中獎……"

    Lottery.objects.filter(id=lottery.id).update(nth=F('nth') + 1, gold=gold)
    push_log("彩券", f"第{lottery.nth}期{lottery.name}開獎結果為{number}號：{message}")
