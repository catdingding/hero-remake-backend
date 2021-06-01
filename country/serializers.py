from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from country.models import Country, CountryOfficial, CountryJoinRequest
from item.models import Item
from chara.models import Chara
from town.models import Town


class CountrySerializer(BaseModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']


class CountryProfileSerializer(BaseModelSerializer):
    location_count = serializers.IntegerField()
    expandable_fields = {
        'king': ('chara.serializers.CharaProfileSerializer', {'fields': ['id', 'name']}),
        'locations': ('world.serializers.LocationSerializer', {'fields': ['id', 'x', 'y'], 'many': True})
    }

    class Meta:
        model = Country
        fields = ['id', 'name', 'gold', 'location_count', 'created_at']


class FoundCountrySerializer(BaseModelSerializer):
    class Meta:
        model = Country
        fields = ['name']

    def save(self):
        country = Country.objects.create(name=self.validated_data['name'], king=self.chara)
        self.chara.location.country = country
        self.chara.location.save()

        self.chara.gold -= 5000000000
        self.chara.lose_items('bag', [Item(type_id=472, number=50)])
        self.chara.country = country
        self.chara.save()

    def validate(self, data):
        location = self.chara.location.lock()
        if self.chara.country is not None:
            raise serializers.ValidationError("僅無所屬角色可以建國")
        if location.country is not None:
            raise serializers.ValidationError("僅可於無所屬城鎮建國")
        if self.chara.gold < 5000000000:
            raise serializers.ValidationError("你的資金不足 50 億")
        return data


class CountryJoinRequestSerializer(BaseModelSerializer):
    chara_name = serializers.CharField(source='chara.name')

    class Meta:
        model = CountryJoinRequest
        fields = ['id', 'chara_name', 'created_at']


class CountryJoinRequestCreateSerializer(BaseModelSerializer):
    class Meta:
        model = CountryJoinRequest
        fields = ['country']

    def create(self, validated_data):
        return CountryJoinRequest.objects.create(chara=self.chara, country=validated_data['country'])

    def validate(self, data):
        if self.chara.country:
            raise serializers.ValidationError("已有所屬國家")
        if CountryJoinRequest.objects.filter(chara=self.chara, country=data['country']).exists():
            raise serializers.ValidationError("已提出過申請")
        return data


class CountryJoinRequestApproveSerializer(BaseSerializer):
    def save(self):
        chara = self.instance.chara.lock()

        if chara.country:
            raise serializers.ValidationError("該角色已加入國家")

        chara.country = self.country
        chara.save()

        CountryJoinRequest.objects.filter(chara=chara).delete()

        self.instance.delete()


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

        chara.country = None
        chara.save()

    def validate_chara(self, chara):
        chara = chara.lock()
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
        if chara == self.chara:
            raise serializers.ValidationError("……禪讓給自己？")
        return chara


class CountryOfficialSerializer(BaseModelSerializer):
    class Meta:
        model = CountryOfficial
        fields = ['id', 'chara', 'title']

    def create(self, validated_data):
        return CountryOfficial.objects.create(country=self.country, **validated_data)

    def validate_chara(self, chara):
        chara = chara.lock()
        if chara.country != self.country:
            raise serializers.ValidationError("不可將官職任命給其他國家的角色")
        return chara


class CountryItemTakeSerializer(BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        item = self.validated_data['item']
        item.number = self.validated_data['number']
        items = [item]

        items = self.country.lose_items(items, mode='return')
        self.chara.get_items("bag", items)


class CountryItemPutSerializer(BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        item = self.validated_data['item']
        item.number = self.validated_data['number']
        items = [item]

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


class CountryOccupyLocationSerializer(BaseSerializer):
    def save(self):
        cost = 2 ** self.country.locations.count()
        self.chara.lose_gold(1000000000 * cost)
        self.chara.lose_items('bag', [Item(type_id=472, number=50 * cost)])
        self.chara.save()

        self.chara.location.country = self.country
        self.chara.location.save()

    def validate(self, data):
        location = self.chara.location.lock()
        if location.country is not None:
            raise serializers.ValidationError("此地已被其他國家佔領")

        return data


class CountryAbandonLocationSerializer(BaseSerializer):
    def save(self):
        self.chara.location.country = None
        self.chara.location.save()

    def validate(self, data):
        location = self.chara.location.lock()
        if location.country != self.chara.country:
            raise serializers.ValidationError("僅可放棄所屬國家的領土")

        return data


class CountryBuildTownSerializer(BaseSerializer):
    name = serializers.CharField(max_length=10)

    def save(self):
        self.chara.lose_gold(1000000000)
        self.chara.lose_items('bag', [Item(type_id=472, number=50)])
        self.chara.save()

        Town.objects.create(name=self.validated_data['name'], location=self.chara.location)

    def validate(self, data):
        location = self.chara.location.lock()
        if location.country != self.chara.country:
            raise serializers.ValidationError("僅可在所屬國家領土建立城鎮")
        if hasattr(location, 'town'):
            raise serializers.ValidationError("該位置已有城鎮")

        return data
