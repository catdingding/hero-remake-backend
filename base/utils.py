from numba import jit, int32
import random

from rest_framework.exceptions import APIException


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


def get_items(field, items):
    exists_item_by_type = {
        item.type_id: item for item in
        field.filter(type__in=[x.type for x in items if x.type.category_id != 1])
    }

    for item in items:
        if item.type_id in exists_item_by_type:
            exists_item_by_type[item.type_id].number += item.number
            exists_item_by_type[item.type_id].save()
        else:
            if item.id is None:
                item.save()
            field.add(item)


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
        if item.id in exists_item_by_id:
            exists_item = exists_item_by_id[item.id]
        elif item.type_id in exists_item_by_type:
            exists_item = exists_item_by_type[item.type_id]
        else:
            raise APIException(f"未擁有{item.type.name}", 400)

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
            raise APIException(f"{item.type.name}數量不足", 400)

        if mode == 'return':
            return return_items
