from django.db.models import Q, Exists, OuterRef
from django.utils.timezone import localtime

from rest_framework import viewsets, views, generics, exceptions

from chara.models import Chara
from country.models import Country, CountryOfficial


class BaseViewSet(viewsets.ViewSet):
    pass


class BaseGenericAPIView(generics.GenericAPIView):
    pass


class CharaViewMixin:
    def get_chara(self, lock=False, check_next_action_time=False):
        queryset = self.request.user.charas.filter(id=self.kwargs['chara_id'])
        if lock:
            queryset = queryset.select_for_update()

        chara = queryset.first()
        if chara is None:
            raise exceptions.PermissionDenied("角色錯誤")

        if check_next_action_time:
            waiting_time = (chara.next_action_time - localtime()).total_seconds()
            if waiting_time > 0:
                raise exceptions.APIException(f"尚需等待{waiting_time}秒才能行動")
        return chara


class CountryViewMixin:
    def get_country(self, role=None, lock=False):
        user = self.request.user
        queryset = Country.objects.filter(id=self.kwargs['country_id'])

        is_king = Exists(Chara.objects.filter(user=user, id=OuterRef('king')))
        is_official = Exists(CountryOfficial.objects.filter(chara__user=user, country=OuterRef('id')))
        is_citizen = Exists(Chara.objects.filter(user=user, country=OuterRef('id')))
        if role == 'king':
            queryset = queryset.filter(is_king)
        elif role == 'official':
            queryset = queryset.filter(is_king | is_official)
        elif role == 'citizen':
            queryset = queryset.filter(is_citizen)
        elif role is not None:
            raise Exception("ilegal role setting")

        if lock:
            queryset = queryset.select_for_update()

        country = queryset.first()
        if country is None:
            raise exceptions.PermissionDenied("國家錯誤")
        return country
