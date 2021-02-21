from datetime import date

from item.models import ItemType


def get_event_item_type():
    today = date.today()
    month = today.month
    day = today.day

    if (month == 1 and day >= 18) or (month == 2):
        return ItemType.objects.get(id=996)  # 紅包
    if month == 5 and day <= 8:
        return ItemType.objects.get(id=997)  # 康乃馨
    if month == 5 and day >= 20:
        return ItemType.objects.get(id=998)  # 肉粽
    if month == 7 or month == 8:
        return ItemType.objects.get(id=999)  # 七彩冰棒
    if month == 9:
        return ItemType.objects.get(id=1000)  # 生日蛋糕
    if month == 10 and day >= 20:
        return ItemType.objects.get(id=1001)  # 萬聖糖
    if (month == 11 and day >= 16) or (month == 12):
        return ItemType.objects.get(id=1002)  # 聖誕玩偶
