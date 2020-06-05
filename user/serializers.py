from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from world.models import AttributeType, Location, SlotType
from user.models import User
from chara.models import Chara, CharaAttribute, CharaSlot


class RegistrationCharaSerializer(BaseModelSerializer):
    class Meta:
        model = Chara
        fields = ['name', 'element_type']

    def validate_name(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("此角色名稱已被使用")
        return value


class RegistrationSerializer(BaseSerializer):
    email = serializers.EmailField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()
    chara = RegistrationCharaSerializer()

    def create(self, validated_data):
        chara_data = validated_data.pop('chara')

        user = User(email=validated_data['email'])
        user.set_password(validated_data['password1'])
        user.save()

        location = Location.objects.get(x=0, y=0)
        chara = Chara.objects.create(user=user, hp=50, mp=10, hp_max=50, mp_max=10,
                                     job_id=1, location=location, **chara_data)
        CharaAttribute.objects.bulk_create([
            CharaAttribute(chara=chara, type=attr_type, value=20, limit=200)
            for attr_type in AttributeType.objects.all()
        ])
        CharaSlot.objects.bulk_create([CharaSlot(chara=chara, type=slot_type) for slot_type in SlotType.objects.all()])

        return user

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("此 email 已被註冊")
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("兩次輸入的密碼不一致")
        return data
