from rest_framework.exceptions import APIException

USE_EFFECT_CLASSES = {}


class UseEffectMeta(type):
    def __new__(cls, name, bases, namespace):
        if name != 'BaseUseEffect':
            cls_id = namespace['id']
            if cls_id in USE_EFFECT_CLASSES:
                raise Exception("class id duplicated")
            USE_EFFECT_CLASSES[dct['id']] = cls

            if 'execute' not in namespace:
                raise Exception("execute method must been implemented")

        return type.__new__(cls, name, bases, dct)


class BaseUseEffect(metaclass=UseEffectMeta):
    def __init__(self, item, n, chara):
        self.item = item
        self.type = item.type
        self.n = n
        self.chara = chara


# 熟練之書
class UseEffect_1(BaseUseEffect):
    id = 1

    def execute(self):
        value = self.type.power * self.n
        self.chara.proficiency += value
        self.chara.save()

        return f"使用了{n}個熟練之書，獲得了{value}點熟練。"


# 屬性熟書
class UseEffect_2(BaseUseEffect):
    id = 2

    def execute(self):
        value = self.type.power * self.n
        chara_attr = self.chara.attributes.get(type=self.type.attribute_type)
        chara_attr.proficiency += value
        chara_attr.save()

        return f"使用了{n}個熟練之書，獲得了{value}點熟練。"


# 提升屬性上限
class UseEffect_3(BaseUseEffect):
    id = 3

    def execute(self):
        value = self.type.power * self.n
        if self.type.rank == 0:
            maxima = 500
        elif self.type.rank == 1:
            maxima = 1200

        chara_attr = self.chara.attributes.get(type=self.type.attribute_type)
        chara_attr.limit = max(chara_attr.limit, min(chara_attr.limit + value, maxima))
        chara_attr.save()

        return f"使用了{n}個{self.type.name}，上限變為{chara_attr.limit}點。"


# 轉屬道具
class UseEffect_4(BaseUseEffect):
    id = 4

    def execute(self):
        self.chara.element_type = self.type.element_type
        self.chara.save()
        return f"使用了{self.type.name}，角色屬性變更為{self.type.element_type.name}屬性。"
