from django.db import models

from rest_framework.exceptions import APIException

from base.models import BaseModel


class Country(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    king = models.ForeignKey("chara.Chara", null=True, related_name="king_of", on_delete=models.SET_NULL)

    gold = models.BigIntegerField(default=0)
    items = models.ManyToManyField("item.Item")

    def get_items(self, items):
        exists_item_by_type = {
            item.type_id: item for item in
            self.items.filter(type__in=[x.type for x in items if x.type.category_id != 1])
        }

        for item in items:
            if item.type_id in exists_item_by_type:
                exists_item_by_type[item.type_id].number += item.number
                exists_item_by_type[item.type_id].save()
            else:
                item.id = None
                item.save()
                self.items.add(item)

    def lose_items(self, items):
        exists_item_by_id = {
            item.id: item for item in
            self.items.filter(id__in=[x.id for x in items if x.id is not None])
        }
        exists_item_by_type = {
            item.type_id: item for item in
            self.items.filter(type__in=[x.type_id for x in items if x.type_id is not None])
        }
        for k, v in exists_item_by_type.items():
            exists_item_by_type[k] = exists_item_by_id.get(v.id, v)

        for item in items:
            if item.id in exists_item_by_id:
                exists_item = exists_item_by_id[item.id]
            elif item.type_id in exists_item_by_type:
                exists_item = exists_item_by_type[item.type_id]
            else:
                raise APIException(f"國庫中沒有{item.type.name}", 400)

            exists_item.number -= item.number

            if exists_item.number > 0:
                exists_item.save()
            elif exists_item.number == 0:
                exists_item.delete()
            else:
                raise APIException(f"國庫中的{item.type.name}數量不足", 400)


class CountryOfficial(BaseModel):
    country = models.ForeignKey("country.Country", related_name="officials", on_delete=models.CASCADE)
    chara = models.OneToOneField("chara.Chara", related_name="official", on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
