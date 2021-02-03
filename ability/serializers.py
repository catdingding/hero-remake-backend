from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from ability.models import Ability, AlchemyOption
from chara.models import Chara
from item.models import Item


class LearnAbilitySerializer(BaseSerializer):
    ability = serializers.PrimaryKeyRelatedField(queryset=Ability.objects.all())

    def save(self):
        ability = self.validated_data['ability']

        self.chara.abilities.add(ability)
        self.chara.proficiency -= ability.require_proficiency
        self.chara.save()

    def validate_ability(self, ability):
        if self.chara.proficiency < ability.require_proficiency:
            raise serializers.ValidationError("熟練度不足")
        if self.chara.job.attribute_type != ability.attribute_type:
            raise serializers.ValidationError("無法學習該系奧義")
        if self.chara.job.rank < ability.rank:
            raise serializers.ValidationError("無法學習該級別奧義")
        if ability.prerequisite is not None:
            if not self.chara.abilities.filter(pk=ability.prerequisite.pk).exists():
                raise serializers.ValidationError("需先學習前置奧義")
        return ability


class AbilitySerializer(BaseModelSerializer):
    is_live = serializers.BooleanField(source='type.is_live')

    class Meta:
        model = Ability
        fields = ['id', 'name', 'attribute_type', 'require_proficiency', 'description', 'is_live']


class SetAbilitySerializer(BaseModelSerializer):
    class Meta:
        model = Chara
        fields = ['main_ability', 'job_ability', 'live_ability']

    def save(self, *args, **kwargs):
        self.update(self.chara, self.validated_data)

    def validate_main_ability(self, ability):
        if ability is None:
            return ability

        self.is_learned_ability(ability)
        return ability

    def validate_job_ability(self, ability):
        if ability is None:
            return ability

        self.is_learned_ability(ability)
        if self.chara.job.attribute_type != ability.attribute_type:
            raise serializers.ValidationError("無法將該奧義裝備為職業奧義")
        return ability

    def validate_live_ability(self, ability):
        if ability is None:
            return ability

        self.is_learned_ability(ability)
        if not ability.type.is_live:
            raise serializers.ValidationError("無法將該奧義裝備為生活奧義")
        return ability

    def is_learned_ability(self, ability):
        if not self.chara.abilities.filter(pk=ability.pk).exists():
            raise serializers.ValidationError("尚未習得此奧義")


class AlchemyOptionSerializer(BaseModelSerializer):
    class Meta:
        model = AlchemyOption
        fields = ['id', 'item_type', 'proficiency_cost']


class AlchemyMakeSerializer(BaseSerializer):
    number = serializers.IntegerField(min_value=1)

    def save(self):
        number = self.validated_data['number']

        self.chara.lose_proficiency(self.instance.proficiency_cost * number)
        self.chara.save()

        self.chara.get_items('bag', self.instance.item_type.make(number))
