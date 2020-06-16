from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from country.models import Country, CountryOfficial
from item.models import Item
from chara.models import Chara

from item.serializers import ItemWithNumberSerializer


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

        CountryOfficial.objects.filter(chara=chara).delete()
        chara.country = None
        chara.save()

    def validate(self, data):
        chara = self.instance
        if chara.country is None:
            raise serializers.ValidationError("無所屬角色無法離開國家")
        if chara.country.king == chara:
            raise serializers.ValidationError("國王無法離開國家")
        return data


class CountryDismissSerializer(BaseSerializer):
    chara = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    def save(self):
        chara = self.validated_data['chara']

        CountryOfficial.objects.filter(chara=chara).delete()
        chara.country = None
        chara.save()

    def validate_chara(self, chara):
        country = self.instance
        if chara.country != country:
            raise serializers.ValidationError("不可開除其他國家的角色")
        if country.king == chara:
            raise serializers.ValidationError("無法開除國王")
        if country.officials.filter(chara=chara).exists():
            raise serializers.ValidationError("無法開除官員")
        return chara


class ChangeKingSerializer(BaseSerializer):
    chara = serializers.PrimaryKeyRelatedField(queryset=Chara.objects.all())

    def save(self):
        country = self.instance
        chara = self.validated_data['chara']

        CountryOfficial.objects.filter(chara=chara).delete()
        country.king = chara
        country.save()

    def validate_chara(self, chara):
        country = self.instance
        if chara.country != country:
            raise serializers.ValidationError("不可將王位交給其他國家的角色")
        return chara


class OfficialSerializer(BaseModelSerializer):
    class Meta:
        model = CountryOfficial
        fields = ['chara', 'title']
        extra_kwargs = {
            'chara': {'validators': []},
        }


class SetOfficialsSerializer(BaseSerializer):
    officials = OfficialSerializer(many=True)

    def save(self):
        country = self.instance
        CountryOfficial.objects.filter(country=country).delete()
        CountryOfficial.objects.bulk_create([
            CountryOfficial(country=country, **official)
            for official in self.validated_data['officials']
        ], ignore_conflicts=True)

    def validate_officials(self, officials):
        country = self.instance
        for official in officials:
            if official['chara'].country != country:
                raise serializers.ValidationError("不可將官職任命給其他國家的角色")
            if official['chara'].country == country.king:
                raise serializers.ValidationError("不可將官職任命給國王")
        return officials


class CountryItemTakeSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)

    def save(self):
        chara = self.instance
        country = chara.country
        items = self.validated_data['items']

        items = country.lose_items(items, mode='return')
        chara.get_items("bag", items)


class CountryItemPutSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)

    def save(self):
        chara = self.instance
        country = chara.country
        items = self.validated_data['items']

        items = chara.lose_items("bag", items, mode='return')
        country.get_items(items)


class CountryDonateSerializer(BaseSerializer):
    gold = serializers.IntegerField(min_value=1)

    def save(self):
        chara = self.instance
        country = chara.country
        gold = self.validated_data['gold']

        chara.gold -= gold
        country.gold += gold

        chara.save()
        country.save()

    def validate_gold(self, gold):
        chara = self.instance
        if gold > chara.gold:
            raise serializers.ValidationError("金錢不足")
        return gold
