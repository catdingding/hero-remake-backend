from base.utils import add_class
from chara.achievement import update_achievement_counter
from system.utils import push_log

EVENT_EFFECT_CLASSES = {}


class BaseEventEffect():
    def __init__(self, event, chara, record):
        self.event = event
        self.type = event.type
        self.chara = chara
        self.record = record


# 獲得奧義
@add_class(EVENT_EFFECT_CLASSES)
class EventEffect_1(BaseEventEffect):
    id = 1

    def execute(self):
        self.record.abilities.add(self.event.param_1)

        return f"效果：{self.event.name}"
