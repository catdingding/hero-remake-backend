from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from country.models import Country, CountryOfficial
from item.models import Item
from chara.models import Chara

from item.serializers import ItemWithNumberSerializer


class CountrySerializer(BaseModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']


class FoundCountrySerializer(BaseModelSerializer):
    class Meta:
        model = Country
        fields = ['name']

    def save(self):
        town = self.chara.location.town

        country = Country.objects.create(name=self.validated_data['name'], king=self.chara)
        town.country = country
        town.save()

        self.chara.gold -= 5000000000
        self.chara.lose_items('bag', [Item(type_id=472, number=50)])
        self.chara.country = country
        self.chara.save()

    def validate(self, data):
        location = self.chara.location.lock()
        if self.chara.country is not None:
            raise serializers.ValidationError("僅無所屬角色可以建國")
        if not hasattr(location, 'town'):
            raise serializers.ValidationError("需於有城鎮的地點建國")
        if location.town.country is not None:
            raise serializers.ValidationError("僅可於無所屬城鎮建國")
        if self.chara.gold < 5000000000:
            raise serializers.ValidationError("你的資金不足 50 億")
        return data


class JoinCountrySerializer(BaseSerializer):
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())

    def save(self):
        self.chara.country = self.validated_data['country']
        self.chara.save()

    def validate(self, data):
        if self.chara.country is not None:
            raise serializers.ValidationError("僅無所屬角色可以入國")
        return data


class LeaveCountrySerializer(BaseSerializer):
    def save(self):
        CountryOfficial.objects.filter(chara=self.chara).delete()
        self.chara.country = None
        self.chara.save()

    def validate(self, data):
        if self.chara.country is None:
            raise serializers.ValidationError("無所屬角色無法離開國家")
        if self.chara.country.king == self.chara:
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
        country = self.country
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
        chara = self.validated_data['chara']

        CountryOfficial.objects.filter(chara=chara).delete()
        self.country.king = chara
        self.country.save()

    def validate_chara(self, chara):
        if chara.country != self.country:
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
        country = self.country
        CountryOfficial.objects.filter(country=country).delete()
        CountryOfficial.objects.bulk_create([
            CountryOfficial(country=country, **official)
            for official in self.validated_data['officials']
        ], ignore_conflicts=True)

    def validate_officials(self, officials):
        country = self.country
        for official in officials:
            if official['chara'].country != country:
                raise serializers.ValidationError("不可將官職任命給其他國家的角色")
            if official['chara'].country == country.king:
                raise serializers.ValidationError("不可將官職任命給國王")
        return officials


class CountryItemTakeSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)

    def save(self):
        items = self.validated_data['items']

        items = self.country.lose_items(items, mode='return')
        self.chara.get_items("bag", items)


class CountryItemPutSerializer(BaseSerializer):
    items = ItemWithNumberSerializer(many=True)

    def save(self):
        items = self.validated_data['items']

        items = self.chara.lose_items("bag", items, mode='return')
        self.country.get_items(items)


class CountryDonateSerializer(BaseSerializer):
    gold = serializers.IntegerField(min_value=1)

    def save(self):
        gold = self.validated_data['gold']

        self.chara.gold -= gold
        self.country.gold += gold

        self.chara.save()
        self.country.save()

    def validate_gold(self, gold):
        if gold > self.chara.gold:
            raise serializers.ValidationError("金錢不足")
        return gold
