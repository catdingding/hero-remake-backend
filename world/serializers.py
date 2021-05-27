from django.db.models import Q
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from country.serializers import CountrySerializer
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
        distance = calculate_distance(self.chara.location, location)

        self.chara.location = location
        self.chara.set_next_action_time(distance)
        self.chara.save()

    def validate_location(self, value):
        x = value.x
        y = value.y
        can_move_to = Location.objects.filter(
            Q(x__gte=x - 1, x__lte=x + 1, y=y) | Q(y__gte=y - 1, y__lte=y + 1, x=x), chaos_score=0
        ).exists()

        if not can_move_to:
            raise serializers.ValidationError("無法前往該地點")
        return value


class MapQuerySerializer(BaseSerializer):
    x = serializers.IntegerField()
    y = serializers.IntegerField()
    radius = serializers.IntegerField(min_value=1, max_value=5)


class LocationSerializer(BaseModelSerializer):
    element_type = ElementTypeSerializer()
    battle_map_name = serializers.CharField(source="battle_map.name")
    country = CountrySerializer(fields=['id', 'name'])
    town_name = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['id', 'x', 'y', 'element_type', 'chaos_score',
                  'battle_map', 'battle_map_name', 'country', 'town_name']

    def get_town_name(self, obj):
        if hasattr(obj, 'town'):
            return obj.town.name
        else:
            return None
