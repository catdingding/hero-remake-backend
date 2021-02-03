from django.db.models import Q, Exists, OuterRef
from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin

from chara.models import CharaAttribute
from job.models import Job, Skill, JobAttribute, ExerciseReward
from job.serializers import (
    JobSerializer, ChangeJobSerializer, SetSkillSettingSerializer, SkillSerializer, ExerciseSerializer, ExerciseRewardSerializer
)


class AvailableJobView(BaseGenericAPIView):
    serializer_class = JobSerializer

    def get(self, request):
        chara = self.get_chara()
        jobs = Job.objects.filter(
            ~ Exists(JobAttribute.objects.filter(job=OuterRef('id')).filter(
                Exists(CharaAttribute.objects.filter(
                    chara=chara,
                    type=OuterRef('type'),
                ).filter(
                    Q(value__lt=OuterRef('require_value')) | Q(proficiency__lt=OuterRef('require_proficiency'))
                ))
            ))
        )
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)


class ChangeJobView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = ChangeJobSerializer


class SetSkillView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SetSkillSettingSerializer


class AvailableSkillView(BaseGenericAPIView):
    serializer_class = SkillSerializer

    def get(self, request):
        chara = self.get_chara()
        skills = Skill.objects.filter(
            Q(is_general=True) | Q(attribute_type=chara.job.attribute_type, rank__lte=chara.job.rank)
        )
        serializer = self.get_serializer(skills, many=True)
        return Response(serializer.data)


class ExerciseView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = ExerciseSerializer


class ExerciseRewardView(ListModelMixin, BaseGenericAPIView):
    serializer_class = ExerciseRewardSerializer
    queryset = ExerciseReward.objects.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
