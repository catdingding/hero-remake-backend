from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from ability.models import AlchemyOption
from item.serializers import ItemTypeSerializer


class AlchemyOptionSerializer(BaseModelSerializer):
    item_type = ItemTypeSerializer(fields=['name'])

    class Meta:
        model = AlchemyOption
        fields = ['id', 'item_type', 'proficiency_cost']


class AlchemyMakeSerializer(BaseSerializer):
    number = serializers.IntegerField(min_value=1)

    def save(self):
        number = self.validated_data['number']

        self.chara.lose_proficiency(self.instance.proficiency_cost * number)
        self.chara.save()

        self.chara.get_items('bag', self.instance.item_type.make(number))
