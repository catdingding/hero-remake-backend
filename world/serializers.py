from django.db.models import Q
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from country.serializers import CountrySerializer
from town.serializers import TownSerializer
from world.models import Location, ElementType, AttributeType, SlotType
from base.utils import calculate_distance


class AttributeTypeSerializer(BaseModelSerializer):
    class Meta:
        model = AttributeType
        fields = ['id', 'name', 'class_name']


class SlotTypeSerializer(BaseModelSerializer):
    class Meta:
        model = SlotType
        fields = ['id', 'name']


class ElementTypeSerializer(BaseModelSerializer):
    class Meta:
        model = ElementType
        fields = ['id', 'name']


class MoveSerializer(BaseSerializer):
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())

    def save(self):
        location = self.validated_data['location']
        cost = calculate_distance(self.chara.location, location)
        # 奧義類型17:飛行
        if self.chara.abilities.filter(type=17).exists():
            cost = cost / 5

        self.chara.location = location
        self.chara.set_next_action_time(cost)
        self.chara.save()


class MapQuerySerializer(BaseSerializer):
    x = serializers.IntegerField()
    y = serializers.IntegerField()
    radius = serializers.IntegerField(min_value=1, max_value=5)


class LocationSerializer(BaseModelSerializer):
    element_type = ElementTypeSerializer()
    battle_map_name = serializers.CharField(source="battle_map.name")
    country = CountrySerializer()
    town = TownSerializer()

    class Meta:
        model = Location
        fields = ['id', 'x', 'y', 'element_type',
                  'battle_map', 'battle_map_name', 'country', 'town']
