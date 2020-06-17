from django.db.models import Q
from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.response import Response

from ability.models import Ability
from ability.serializers import LearnAbilitySerializer, AbilitySerializer, SetAbilitySerializer


class LearnAbilityView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = LearnAbilitySerializer


class AvailableToLearnAbilityView(BaseGenericAPIView):
    serializer_class = AbilitySerializer

    def get(self, request, chara_id):
        chara = self.get_chara()

        abilities = Ability.objects.filter(Q(prerequisite__in=chara.abilities.all()) | Q(prerequisite__isnull=True),
                                           ~Q(id__in=chara.abilities.all()),
                                           attribute_type=chara.job.attribute_type, rank__lte=chara.job.rank)
        abilities = abilities.select_related('type')

        serializer = self.get_serializer(abilities, many=True)
        return Response(serializer.data)


class SetAbilityView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = SetAbilitySerializer


class AvailableToSetAbilityView(BaseGenericAPIView):
    serializer_class = AbilitySerializer

    def get(self, request, chara_id):
        chara = self.get_chara()

        abilities = chara.abilities.filter(type__need_equip=True).select_related('type')

        serializer = self.get_serializer(abilities, many=True)
        return Response(serializer.data)
