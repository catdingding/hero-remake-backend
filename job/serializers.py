import random

from rest_framework import serializers

from base.utils import randint
from base.serializers import BaseSerializer, BaseModelSerializer

from job.models import Job, Skill, ExerciseReward, JobAttribute
from chara.models import CharaSkillSetting, CharaAttribute

from chara.serializers import CharaSkillSettingSerializer
from world.serializers import AttributeTypeSerializer

from system.utils import push_log


class JobAttributeSerializer(BaseModelSerializer):
    type = AttributeTypeSerializer()

    class Meta:
        model = JobAttribute
        fields = ['type', 'require_value', 'require_proficiency']


class JobSerializer(BaseModelSerializer):
    attribute_type = AttributeTypeSerializer()
    attributes = JobAttributeSerializer(many=True)
    is_available = serializers.BooleanField()

    class Meta:
        model = Job
        fields = ['id', 'name', 'attribute_type', 'rank', 'description', 'attributes', 'is_available']


class ChangeJobSerializer(BaseSerializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())

    def save(self):
        chara = self.chara
        job = self.validated_data['job']

        # calculat bonus
        total_battle_bonus = min(200, chara.record.total_battle // 2000)

        # calculate attributes
        for job_attr in job.attributes.all():
            chara_attr = chara.attrs[job_attr.type.en_name]

            current_bonus = random.randint(0, round(chara_attr.value / 1.5))
            prof_bonus = round(chara_attr.proficiency ** 0.375)

            new_attr_value = job_attr.base_value + current_bonus + prof_bonus + total_battle_bonus
            chara_attr.value = min(chara_attr.limit, max(30, new_attr_value))

            if chara_attr.type_id != job.attribute_type_id:
                chara_attr.value = min(1200, chara_attr.value)

        # calculate hp / mp
        chara.hp_max = min(chara.hp_limit, max(30, random.randint(0, round(chara.hp_max / 1.5)) + job.base_hp))
        chara.mp_max = min(chara.mp_limit, max(30, random.randint(0, round(chara.mp_max / 1.5)) + job.base_mp))
        chara.hp = chara.hp_max
        chara.mp = chara.mp_max

        # reset chara data
        chara.exp = 0
        if chara.job.attribute_type != job.attribute_type:
            chara.job_ability = None
            chara.skill_settings.all().delete()

        CharaAttribute.objects.bulk_update(chara.attrs.values(), fields=['value'])
        chara.job = job
        chara.save()

        chara.record.level_down_count = 0
        chara.record.save()

    def validate_job(self, job):
        for job_attr in job.attributes.all():
            attr_type = job_attr.type.en_name
            if job_attr.require_value > self.chara.attrs[attr_type].value:
                raise serializers.ValidationError("能力不足")
            if job_attr.require_proficiency > self.chara.attrs[attr_type].proficiency:
                raise serializers.ValidationError("職業熟練不足")

        return job

    def validate(self, data):
        if self.chara.level < 100:
            raise serializers.ValidationError("等級不足 100")
        return data


class SkillSerializer(BaseModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'power', 'rate', 'mp_cost']


class SetSkillSettingSerializer(BaseSerializer):
    settings = CharaSkillSettingSerializer(many=True)

    def save(self):
        CharaSkillSetting.objects.filter(chara=self.chara).delete()
        CharaSkillSetting.objects.bulk_create([
            CharaSkillSetting(chara=self.chara, **setting)
            for setting in self.validated_data['settings']
        ])

    def validate_settings(self, settings):
        if len(settings) > 10:
            raise serializers.ValidationError("不可設定超過10項")

        for setting in settings:
            skill = setting['skill']
            if skill.is_general:
                continue
            if skill.attribute_type != self.chara.job.attribute_type:
                raise serializers.ValidationError("無法使用該類型技能")
            if skill.rank > self.chara.job.rank:
                raise serializers.ValidationError("無法使用該級別技能")
        return settings


class ExerciseSerializer(BaseSerializer):
    def save(self):
        self.chara.proficiency -= self.validated_data['proficiency_cost']
        self.chara.save()

        if randint(1, 100) == 1:
            rate = 15
        elif randint(1, 15) == 1:
            rate = 5
        else:
            rate = 1

        for reward in self.chara.job.attribute_type.exercise_rewards.all():
            attr = self.chara.attrs[reward.reward_attribute_type.en_name]
            limit_growth = reward.limit_growth * rate

            if attr.limit < 400:
                attr.limit += limit_growth

        CharaAttribute.objects.bulk_update(self.chara.attrs.values(), fields=['limit'])

        if rate > 1:
            push_log("成長", f"{self.chara.name}的屬性上限在修煉後急速的上升了")

    def validate(self, data):
        cost = (sum(attr.limit for attr in self.chara.attrs.values()) - 1000) // 20
        cost = min(10000, cost ** 2)
        if cost > self.chara.proficiency:
            raise serializers.ValidationError("熟練度不足")
        data['proficiency_cost'] = cost
        return data


class ExerciseRewardSerializer(BaseModelSerializer):
    job_attribute_type = AttributeTypeSerializer()
    reward_attribute_type = AttributeTypeSerializer()

    class Meta:
        model = ExerciseReward
        fields = ['job_attribute_type', 'reward_attribute_type', 'limit_growth']
