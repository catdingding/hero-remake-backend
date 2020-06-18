import random

from rest_framework import serializers
from base.serializers import BaseSerializer, BaseModelSerializer

from job.models import Job, Skill
from chara.models import CharaSkillSetting, CharaAttribute


class JobSerializer(BaseModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'name', 'attribute_type', 'rank', 'description']


class ChangeJobSerializer(BaseSerializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())

    def save(self):
        chara = self.chara
        job = self.validated_data['job']

        # calculat bonus
        level_up_bonus = min(50, chara.record.monthly_level_up // 100)
        total_battle_bonus = min(100, chara.record.total_battle // 2000)

        # calculate attributes
        for job_attr in job.attributes.all():
            chara_attr = chara.attrs[job_attr.type_id]

            current_bonus = random.randint(0, round(chara_attr.value / 1.5))
            prof_bonus = round(chara_attr.proficiency ** 0.375)

            new_attr_value = job_attr.base_value + current_bonus + prof_bonus + level_up_bonus + total_battle_bonus
            chara_attr.value = min(chara_attr.limit, max(30, new_attr_value))

            if chara_attr.type_id != job.attribute_type:
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

    def validate_job(self, job):
        for job_attr in job.attributes.all():
            attr_type = job_attr.type_id
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
        fields = ['name', 'power', 'rate', 'mp_cost']


class CharaSkillSettingSerializer(BaseModelSerializer):
    class Meta:
        model = CharaSkillSetting
        fields = ['skill', 'hp_percentage', 'mp_percentage', 'order']


class SetSkillSettingSerializer(BaseSerializer):
    settings = CharaSkillSettingSerializer(many=True)

    def save(self):
        CharaSkillSetting.objects.bulk_create([
            CharaSkillSetting(chara=self.chara, **setting)
            for setting in self.validated_data['settings']
        ])

    def validate_settings(self, settings):
        if len(settings) > 10:
            raise serializers.ValidationError("不可設定超過10項")

        for setting in settings:
            skill = settings.skill
            if skill.attribute_type != self.chara.job.attribute_type:
                raise serializers.ValidationError("無法使用該類型技能")
            if skill.rank > self.chara.job.rank:
                raise serializers.ValidationError("無法使用該級別技能")
        return settings
