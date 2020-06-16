from django.db.models import Q, Exists, OuterRef
from django.utils.timezone import localtime

from rest_framework import viewsets, views, generics, exceptions

from chara.models import Chara
from country.models import Country, CountryOfficial

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
    def get_country(self, role, lock=False):
        chara = self.get_chara()
        country = chara.country

        if country is None:
            raise exceptions.APIException(f"未加入國家")

        if role == 'king':
            pass_role_check = (country.king == chara)
        elif role == 'official':
            pass_role_check = (country.king == chara) or (country.officials.filter(chara=chara).exists())
        elif role == 'citizen':
            pass_role_check = True
        else:
            raise Exception("ilegal role setting")

        if not pass_role_check:
            raise exceptions.APIException(f"沒有足夠的對國家權限")

        if lock:
            country = country.lock()

        return country


class BaseViewSet(CountryViewMixin, CharaViewMixin, viewsets.ViewSet):
    pass


class BaseGenericAPIView(CountryViewMixin, CharaViewMixin, generics.GenericAPIView):
    pass
