from rest_framework import serializers
from base.serializers import (
    BaseSerializer, BaseModelSerializer,
    SerpyModelSerializer
)
from django.utils.timezone import localtime
from datetime import timedelta

from home.models import FarmingReward
from chara.models import CharaFarm
from item.models import Item


class CharaFarmExpandSerializer(BaseSerializer):
    def save(self):
        self.chara.lose_gold(100000000)
        self.chara.save()

        CharaFarm.objects.create(chara=self.chara)

    def validate(self, data):
        if self.chara.farms.count() >= 8:
            raise serializers.ValidationError("農地上限為8")
        return data


class CharaFarmPlaceItemSerializer(BaseSerializer):
    farm = serializers.PrimaryKeyRelatedField(queryset=CharaFarm.objects.all())
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())

    def save(self):
        item = self.validated_data['item']
        item.number = 1
        item = self.chara.lose_items('bag', [item], mode='return')[0]
        item.save()

        farm = self.validated_data['farm']
        farm.item = item
        farm.due_time = localtime() + timedelta(hours=8)
        farm.save()

    def validate_farm(self, farm):
        if farm.item:
            raise serializers.ValidationError("已放置物品")
        if farm.chara != self.chara:
            raise serializers.ValidationError("這不是你的農地")
        return farm


class CharaFarmRemoveItemSerializer(BaseSerializer):
    farm = serializers.PrimaryKeyRelatedField(queryset=CharaFarm.objects.all())

    def save(self):
        farm = self.validated_data['farm']
        farm.item.delete()
        farm.item = None
        farm.due_time = None
        farm.save()

    def validate_farm(self, farm):
        if not farm.item:
            raise serializers.ValidationError("未放置物品")
        if farm.chara != self.chara:
            raise serializers.ValidationError("這不是你的農地")
        return farm


class CharaFarmHarvestSerializer(BaseSerializer):
    farm = serializers.PrimaryKeyRelatedField(queryset=CharaFarm.objects.all())

    def save(self):
        farm = self.validated_data['farm']

        reward = FarmingReward.objects.filter(item_type=farm.item.type_id).first()
        if reward:
            item = Item(type=reward.reward_item_type, number=reward.number)
            message = f"收穫了{item.name}*{item.number}"
        elif '券' in farm.item.type.name:
            item = None
            message = f"埋在土裡的{farm.item.name}已經爛掉了……"
        else:
            item = farm.item
            message = f"原封不動的取回了{item.name}"

        if farm.item.id != item.id:
            farm.item.delete()
        if item is not None:
            self.chara.get_items('bag', [item])

        farm.item = None
        farm.due_time = None
        farm.save()

        return {'display_message': message}

    def validate_farm(self, farm):
        if not farm.item:
            raise serializers.ValidationError("未放置物品")
        if farm.due_time > localtime():
            raise serializers.ValidationError("未到收穫時間")
        if farm.chara != self.chara:
            raise serializers.ValidationError("這不是你的農地")
        return farm
