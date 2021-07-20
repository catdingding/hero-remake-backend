from numba import jit, int32
import paramiko
import math
import random

from django.conf import settings
from rest_framework.exceptions import ValidationError


@jit(int32(int32, int32), nopython=True)
def randint(low, high):
    return random.randint(low, high)


def calculate_distance(d1, d2):
    return abs(d1.x - d2.x) + abs(d1.y - d2.y)


def add_class(dictionary):
    def decorator(cls):
        assert cls.id not in dictionary, "id duplicated"
        dictionary[cls.id] = cls
        return cls
    return decorator


def get_items(field, limit, items):
    if not items:
        return

    if field.count() >= limit:
        raise ValidationError("物品已滿")

    exists_item_by_type = {
        item.type_id: item for item in
        field.filter(type__in=[x.type for x in items if x.type.category_id != 1])
    }

    for item in items:
        assert item.number > 0

        if item.type_id in exists_item_by_type:
            exists_item_by_type[item.type_id].number += item.number
            exists_item_by_type[item.type_id].save()
        else:
            if item.id is None:
                item.save()
            field.add(item)

            if item.type.category_id != 1:
                exists_item_by_type[item.type_id] = item


def lose_items(field, items, mode='delete'):
    assert mode in ['delete', 'return']

    exists_item_by_id = {
        item.id: item for item in
        field.filter(id__in=[x.id for x in items if x.id is not None])
    }
    exists_item_by_type = {
        item.type_id: item for item in
        field.filter(type__in=[x.type_id for x in items if x.type_id is not None])
    }
    for k, v in exists_item_by_type.items():
        exists_item_by_type[k] = exists_item_by_id.get(v.id, v)

    return_items = []

    for item in items:
        assert item.number > 0

        if item.id in exists_item_by_id:
            exists_item = exists_item_by_id[item.id]
        elif item.type_id in exists_item_by_type:
            exists_item = exists_item_by_type[item.type_id]
        else:
            raise ValidationError(f"未擁有{item.type.name}")

        if exists_item.number > item.number:
            exists_item.number -= item.number
            exists_item.save()
            if mode == 'return':
                item.id = None
                return_items.append(item)
        elif exists_item.number == item.number:
            if mode == 'delete':
                exists_item.delete()
            elif mode == 'return':
                field.remove(exists_item)
                return_items.append(exists_item)
        else:
            raise ValidationError(f"{item.type.name}數量不足")

        if mode == 'return':
            return return_items


def sftp_put_fo(fo, dest):
    t = paramiko.Transport((settings.SFTP['host'], settings.SFTP['port']))
    t.connect(username=settings.SFTP['user'], password=settings.SFTP['password'])
    sftp = paramiko.SFTPClient.from_transport(t)
    sftp.putfo(fo, dest)
    t.close()


def format_currency(value):
    if value == 0:
        return "0"

    output = ""
    if value >= 100000000:
        output = f"{math.floor(value / 100000000)}億"
        value = value % 100000000

    if value >= 10000:
        output = f"{output}{math.floor(value / 10000)}萬"
        value = value % 10000

    if value >= 1:
        output = f"{output}{value}"

    return output
