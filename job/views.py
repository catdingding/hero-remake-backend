from django.db.models import Q, Exists, OuterRef
from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.response import Response

from job.models import Job, Skill
from job.serializers import JobSerializer, ChangeJobSerializer, SetSkillSettingSerializer, SkillSerializer


class AvailableJobView(BaseGenericAPIView):
    serializer_class = JobSerializer

    def get(self, request):
        chara = self.get_chara()
        jobs = Job.objects.raw("""
            SELECT job.* FROM job_job as job WHERE NOT EXISTS(
                SELECT * FROM job_jobattribute as job_attr INNER JOIN chara_charaattribute as chara_attr
                ON
                    chara_attr.chara_id=%s AND job_attr.type_id = chara_attr.type_id AND
                    (
                        job_attr.require_value > chara_attr.value OR
                        job_attr.require_proficiency > chara_attr.proficiency
                    )
                WHERE job_attr.job_id = job.id
            )
        """, [chara.id])
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
        skills = Skill.objects.filter(attribute_type=chara.job.attribute_type, rank__lte=chara.job.rank)
        serializer = self.get_serializer(skills, many=True)
        return Response(serializer.data)
