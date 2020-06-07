from django.db.models import Q
from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin
from rest_framework.response import Response

from ability.models import Ability
from ability.serializers import LearnAbilitySerializer, AbilitySerializer, SetAbilitySerializer


class LearnAbilityView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = LearnAbilitySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class AvailableToLearnAbilityView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = AbilitySerializer

    def get(self, request, chara_id):
        chara = self.get_chara()

        abilities = Ability.objects.filter(Q(prerequisite__in=chara.abilities.all()) | Q(prerequisite__isnull=True),
                                           ~Q(id__in=chara.abilities.all()),
                                           attribute_type=chara.job.attribute_type, rank__lte=chara.job.rank)
        abilities = abilities.select_related('type')

        serializer = self.get_serializer(abilities, many=True)
        return Response(serializer.data)


class SetAbilityView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = SetAbilitySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class AvailableToSetAbilityView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = AbilitySerializer

    def get(self, request, chara_id):
        chara = self.get_chara()

        abilities = chara.abilities.filter(type__need_equip=True).select_related('type')

        serializer = self.get_serializer(abilities, many=True)
        return Response(serializer.data)
