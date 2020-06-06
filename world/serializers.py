from django.db.models import Q
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from world.models import Location
from base.utils import calculate_distance


class MoveSerializer(BaseSerializer):
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())

    def save(self):
        chara = self.instance
        location = self.validated_data['location']
        distance = calculate_distance(chara.location, location)

        chara.location = location
        chara.set_next_action_time(distance)
        chara.save()

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
    radius = serializers.IntegerField()


class LocationSerializer(BaseModelSerializer):
    battle_map_name = serializers.CharField(source="battle_map.name")
    town_name = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['x', 'y', 'chaos_score', 'battle_map_name', 'town_name']

    def get_town_name(self, obj):
        if hasattr(obj, 'town'):
            return obj.town.name
        else:
            return None
