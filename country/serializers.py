from rest_framework import serializers
import serpy
from base.serializers import (
    BaseSerializer, BaseModelSerializer, TransferPermissionCheckerMixin,
    SerpyModelSerializer, LockedEquipmentCheckMixin
)

from country.models import Country, CountryOfficial, CountryJoinRequest, CountrySetting
from item.models import Item
from chara.models import Chara
from town.models import Town

from chara.achievement import update_achievement_counter
from system.utils import push_log, send_private_message_by_system, send_refresh_chara_profile_signal


class CountrySerializer(SerpyModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']


class CountrySettingUpdateSerialzier(BaseModelSerializer):
    class Meta:
        model = CountrySetting
        fields = ['introduction']


class CountrySettingSerialzier(SerpyModelSerializer):
    class Meta:
        model = CountrySetting
        fields = ['introduction']


class CountryProfileSerializer(SerpyModelSerializer):
    location_count = serpy.Field()
    citizen_count = serpy.Field()
    setting = CountrySettingSerialzier()

    king = serpy.MethodField()
    locations = serpy.MethodField()

    class Meta:
        model = Country
        fields = ['id', 'name', 'gold', 'item_limit', 'location_count', 'citizen_count', 'setting', 'created_at']

    def get_king(self, obj):
        from chara.serializers import CharaProfileSerializer
        return CharaProfileSerializer(obj.king, fields=['id', 'name']).data

    def get_locations(self, obj):
        from world.serializers import LocationSerializer
        return LocationSerializer(obj.locations.all(), many=True, fields=['id', 'x', 'y', 'battle_map_name']).data


class FoundCountrySerializer(BaseModelSerializer):
    class Meta:
        model = Country
        fields = ['name']

    def save(self):
        country = Country.objects.create(name=self.validated_data['name'], king=self.chara)
        CountrySetting.objects.create(country=country)
        self.chara.location.country = country
        self.chara.location.save()

        self.chara.gold -= 5000000000
        self.chara.lose_items('bag', [Item(type_id=472, number=50)])
        self.chara.country = country
        self.chara.save()

        CountryJoinRequest.objects.filter(chara=self.chara).delete()

        push_log("建國", f"{self.chara.name}建立了{country.name}")
        send_refresh_chara_profile_signal(self.chara.id)

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
        join_request = CountryJoinRequest.objects.create(chara=self.chara, country=validated_data['country'])

        send_private_message_by_system(self.chara.id, validated_data['country'].king_id, f"{self.chara.name}發出了入國申請")
        for official in validated_data['country'].officials.all():
            send_private_message_by_system(self.chara.id, official.chara_id, f"{self.chara.name}發出了入國申請")

        return join_request

    def validate(self, data):
        if self.chara.country:
            raise serializers.ValidationError("已有所屬國家")
        if CountryJoinRequest.objects.filter(chara=self.chara, country=data['country']).exists():
            raise serializers.ValidationError("已提出過申請")
        return data


class CountryJoinRequestReviewSerializer(BaseSerializer):
    action = serializers.ChoiceField(choices=['accept', 'reject'])

    def save(self):
        chara = self.instance.chara.lock()

        if self.validated_data['action'] == 'accept':
            if chara.country:
                raise serializers.ValidationError("該角色已加入國家")

            chara.country = self.country
            chara.save()

            CountryJoinRequest.objects.filter(chara=chara).delete()
            push_log("入國", f"{chara.name}加入了{self.country.name}")
            send_refresh_chara_profile_signal(chara.id)
            # 入國次數次數
            update_achievement_counter(chara, 4, 1, 'increase')
            return {'display_message': '入國申請已通過'}

        elif self.validated_data['action'] == 'reject':
            self.instance.delete()
            return {'display_message': '入國申請已拒絕'}


class LeaveCountrySerializer(BaseSerializer):
    def save(self):
        country = self.chara.country

        CountryOfficial.objects.filter(chara=self.chara).delete()
        self.chara.country = None
        self.chara.save()

        push_log("下野", f"{self.chara.name}離開了{country.name}")
        send_refresh_chara_profile_signal(self.chara.id)

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

        send_refresh_chara_profile_signal(chara.id)

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


class CountryOfficialSerializer(SerpyModelSerializer):
    class Meta:
        model = CountryOfficial
        fields = ['id', 'chara', 'title']


class CountryOfficialCreateSerializer(BaseModelSerializer):
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

        push_log("國庫", f"{self.chara.name}自國庫取出了{item.name}*{item.number}")


class CountryItemPutSerializer(LockedEquipmentCheckMixin, TransferPermissionCheckerMixin, BaseSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    number = serializers.IntegerField(min_value=1)

    def save(self):
        item = self.validated_data['item']
        item.number = self.validated_data['number']
        items = [item]

        items = self.chara.lose_items("bag", items, mode='return')
        self.country.get_items(items)

        push_log("國庫", f"{self.chara.name}向國庫存入了{item.name}*{item.number}")


class CountryDonateSerializer(BaseSerializer):
    gold = serializers.IntegerField(min_value=1)

    def save(self):
        gold = self.validated_data['gold']

        self.chara.lose_gold(gold)
        self.country.gold += gold

        self.chara.save()
        self.country.save()

        push_log("國庫", f"{self.chara.name}向國庫捐贈了{gold}金錢")
        # 國家資金捐獻數量
        update_achievement_counter(self.chara, 11, gold, 'increase')

    def validate_gold(self, gold):
        if gold > self.chara.gold:
            raise serializers.ValidationError("金錢不足")
        return gold


class CountryOccupyLocationSerializer(BaseSerializer):
    def save(self):
        cost = 2 ** self.country.locations.count()

        self.country.lose_gold(1000000000 * cost)
        self.country.save()

        self.chara.lose_items('bag', [Item(type_id=472, number=50 * cost)])
        self.chara.save()

        self.chara.location.country = self.country
        self.chara.location.save()

        push_log("建城", f"{self.country.name}佔領了({self.chara.location.x},{self.chara.location.y})")

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
        self.country.lose_gold(1000000000)
        self.country.save()
        self.chara.lose_items('bag', [Item(type_id=472, number=50)])
        self.chara.save()

        town = Town.objects.create(name=self.validated_data['name'], location=self.chara.location)

        push_log("建城", f"{self.chara.country.name}於({self.chara.location.x},{self.chara.location.y})建立了{town.name}")

    def validate(self, data):
        location = self.chara.location.lock()
        if location.country != self.chara.country:
            raise serializers.ValidationError("僅可在所屬國家領土建立城鎮")
        if hasattr(location, 'town'):
            raise serializers.ValidationError("該位置已有城鎮")

        return data


class CountryRenameTownSerializer(BaseSerializer):
    name = serializers.CharField(max_length=10)

    def save(self):
        self.country.lose_gold(500000000)
        self.country.save()

        orig_name = self.chara.location.town.name
        Town.objects.filter(location=self.chara.location).update(name=self.validated_data['name'])

        push_log(
            "城鎮", f"{self.chara.country.name}的{self.chara.name}將({self.chara.location.x},{self.chara.location.y})的{orig_name}改名為{self.validated_data['name']}")

    def validate(self, data):
        location = self.chara.location
        if location.country != self.chara.country:
            raise serializers.ValidationError("僅更名所屬國家領土的城鎮")
        if not hasattr(location, 'town'):
            raise serializers.ValidationError("該位置沒有城鎮")

        return data


class CountryUpgradeStorageSerializer(BaseSerializer):
    def save(self):
        self.country.lose_gold(self.country.item_limit * 1000000)
        self.country.item_limit += 1
        self.country.save()
