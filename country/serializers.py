from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from country.models import Country
from item.models import Item


class FoundCountrySerializer(BaseModelSerializer):
    class Meta:
        model = Country
        fields = ['name']

    def save(self):
        chara = self.instance
        town = chara.location.town

        country = Country.objects.create(name=self.validated_data['name'], king=chara)
        town.country = country
        town.save()

        chara.gold -= 5000000000
        chara.lose_items('bag', [Item(type_id=472, number=50)])
        chara.country = country
        chara.save()

    def validate(self, data):
        chara = self.instance
        location = chara.location.lock()
        if chara.country is not None:
            raise serializers.ValidationError("僅無所屬角色可以建國")
        if not hasattr(location, 'town'):
            raise serializers.ValidationError("需於有城鎮的地點建國")
        if location.town.country is not None:
            raise serializers.ValidationError("僅可於無所屬城鎮建國")
        if chara.gold < 5000000000:
            raise serializers.ValidationError("你的資金不足 50 億")
        return data


class JoinCountrySerializer(BaseSerializer):
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())

    def save(self):
        chara = self.instance

        chara.country = self.validated_data['country']
        chara.save()

    def validate(self, data):
        chara = self.instance
        if chara.country is not None:
            raise serializers.ValidationError("僅無所屬角色可以入國")
        return data


class LeaveCountrySerializer(BaseSerializer):
    def save(self):
        chara = self.instance

        chara.country = None
        chara.save()

    def validate(self, data):
        chara = self.instance
        if chara.country is None:
            raise serializers.ValidationError("無所屬角色無法離開國家")
        if chara.country.king == chara:
            raise serializers.ValidationError("國王無法離開國家")
        return data
