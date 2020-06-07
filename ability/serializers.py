from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from ability.models import Ability


class LearnAbilitySerializer(BaseSerializer):
    ability = serializers.PrimaryKeyRelatedField(queryset=Ability.objects.all())

    def save(self):
        chara = self.instance
        ability = self.validated_data['ability']

        chara.abilities.add(ability)
        chara.proficiency -= ability.require_proficiency
        chara.save()

    def validate_ability(self, ability):
        chara = self.instance
        if chara.proficiency < ability.require_proficiency:
            raise serializers.ValidationError("熟練度不足")
        if chara.job.attribute_type != ability.attribute_type:
            raise serializers.ValidationError("無法學習該系奧義")
        if chara.job.rank < ability.rank:
            raise serializers.ValidationError("無法學習該級別奧義")
        if ability.prerequisite is not None:
            if not chara.abilities.filter(pk=ability.prerequisite.pk).exists():
                raise serializers.ValidationError("需先學習前置奧義")
        return ability


class AbilitySerializer(BaseModelSerializer):
    class Meta:
        model = Ability
        fields = ['name', 'require_proficiency', 'description']
