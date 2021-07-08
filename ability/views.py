from django.db.models import Q, Max
from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaPostViewMixin
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.decorators import action

from ability.models import Ability, AlchemyOption
from ability.serializers import LearnAbilitySerializer, AbilitySerializer, SetAbilitySerializer
from ability.serializers_alchemy import AlchemyOptionSerializer, AlchemyMakeSerializer


class LearnAbilityView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = LearnAbilitySerializer


class AbilityView(ListModelMixin, BaseGenericAPIView):
    serializer_class = AbilitySerializer
    queryset = Ability.objects.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class AvailableToLearnAbilityView(BaseGenericAPIView):
    serializer_class = AbilitySerializer

    def get(self, request):
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

    def get(self, request):
        chara = self.get_chara()

        abilities = chara.abilities.filter(type__need_equip=True).select_related('type')

        serializer = self.get_serializer(abilities, many=True)
        return Response(serializer.data)


class AlchemyOptionViewSet(ListModelMixin, BaseGenericViewSet):
    queryset = AlchemyOption.objects.all()
    serializer_class = AlchemyOptionSerializer
    serializer_action_classes = {
        'make': AlchemyMakeSerializer,
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        alchemy_power = self.get_chara().abilities.filter(type=21).aggregate(power=Max('power'))['power']
        if alchemy_power is None:
            return queryset.filter(pk__isnull=True)
        else:
            return queryset.filter(require_power__lte=alchemy_power)

    @action(methods=['post'], detail=True)
    def make(self, request, pk):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})
