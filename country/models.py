from django.db import models
from rest_framework.exceptions import ValidationError

from base.models import BaseModel
from base.utils import get_items, lose_items


class Country(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    king = models.OneToOneField("chara.Chara", null=True, related_name="king_of", on_delete=models.SET_NULL)

    gold = models.BigIntegerField(default=0)
    items = models.ManyToManyField("item.Item")

    item_limit = models.IntegerField(default=10)

    def get_items(self, *args, **kwargs):
        return get_items(self.items, self.item_limit, *args, **kwargs)

    def lose_items(self, *args, **kwargs):
        return lose_items(self.items, *args, **kwargs)

    def lose_gold(self, number):
        if self.gold < number:
            raise ValidationError("國庫金錢不足")
        self.gold -= number


class CountrySetting(BaseModel):
    country = models.OneToOneField('country.Country', related_name='setting', on_delete=models.CASCADE)

    introduction = models.TextField(blank=True)


class CountryJoinRequest(BaseModel):
    country = models.ForeignKey("country.Country", related_name="country_join_requests", on_delete=models.CASCADE)
    chara = models.ForeignKey("chara.Chara", related_name="country_join_requests", on_delete=models.CASCADE)

    class Meta:
        unique_together = ('country', 'chara')


class CountryOfficial(BaseModel):
    country = models.ForeignKey("country.Country", related_name="officials", on_delete=models.CASCADE)
    chara = models.OneToOneField("chara.Chara", related_name="official", on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
