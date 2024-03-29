from django.contrib.auth.forms import SetPasswordForm
from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer


from world.models import Location
from user.models import User
from chara.models import Chara, CharaAttribute, CharaSlot, CharaIntroduction, CharaRecord

from system.utils import push_log


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
    chara_avatar = serializers.ImageField()

    def create(self, validated_data):
        chara_data = validated_data.pop('chara')

        user = User(email=validated_data['email'])
        user.set_password(validated_data['password1'])
        user.save()

        location = Location.objects.get(x=0, y=0)
        chara = Chara.objects.create(user=user, hp=50, mp=10, hp_max=50, mp_max=10,
                                     job_id=1, location=location, **chara_data)
        chara.init()
        chara.set_avatar(validated_data['chara_avatar'])

        push_log("新人", f"{chara.name}加入了世界")

        return user

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("此 email 已被註冊")
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("兩次輸入的密碼不一致")
        return data


class ChangePasswordSerializer(BaseSerializer):
    old_password = serializers.CharField()
    new_password1 = serializers.CharField()
    new_password2 = serializers.CharField()

    def validate_old_password(self, value):
        if not self.user.check_password(value):
            raise serializers.ValidationError("舊密碼輸入錯誤")
        return value

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError("兩次輸入的新密碼不一致")

        return data

    def save(self):
        self.user.set_password(self.validated_data['new_password1'])
        self.user.save()
