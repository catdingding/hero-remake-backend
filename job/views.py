from django.db.models import Q, Exists, OuterRef
from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin
from rest_framework.response import Response

from job.models import Job, Skill
from job.serializers import JobSerializer, ChangeJobSerializer, SetSkillSettingSerializer, SkillSerializer


class AvailableJobView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = JobSerializer

    def get(self, request, chara_id):
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


class ChangeJobView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = ChangeJobSerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class SetSkillView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = SetSkillSettingSerializer

    def post(self, request, chara_id):
        chara = self.get_chara()
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class AvailableSkillView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = SkillSerializer

    def get(self, request, chara_id):
        chara = self.get_chara()
        skills = Skill.objects.filter(attribute_type=chara.job.attribute_type, rank__lte=chara.job.rank)
        serializer = self.get_serializer(skills, many=True)
        return Response(serializer.data)
