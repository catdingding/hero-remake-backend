from django.db.models import Q, Exists, OuterRef
from django.utils.timezone import localtime
from django.conf import settings

from rest_framework import viewsets, views, generics
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response

from town.models import Town
from chara.models import Chara
from country.models import Country, CountryOfficial


class CharaViewMixin:
    check_next_action_time = False
    check_in_town = False

    def get_chara(self, lock=False):
        queryset = self.request.user.charas.filter(id=int(self.request.headers['Chara-ID']))
        if lock:
            queryset = queryset.select_for_update()

        chara = queryset.first()
        if chara is None:
            raise PermissionDenied("角色錯誤")

        if self.check_next_action_time:
            waiting_time = (chara.next_action_time - localtime()).total_seconds()
            if waiting_time > settings.ACTION_TIME_GRACE:
                raise ValidationError(f"尚需等待{waiting_time}秒才能行動")
        if self.check_in_town:
            if not Town.objects.filter(location=chara.location_id).exists():
                raise ValidationError(f"需位於城鎮中")
        self.request.chara = chara
        return chara


class CountryViewMixin:
    def get_country(self, role, lock=False):
        chara = self.get_chara()
        country = chara.country

        if country is None:
            raise ValidationError(f"未加入國家")

        if role == 'king':
            pass_role_check = (country.king == chara)
        elif role == 'official':
            pass_role_check = (country.king == chara) or (country.officials.filter(chara=chara).exists())
        elif role == 'citizen':
            pass_role_check = True
        else:
            raise Exception("ilegal role setting")

        if not pass_role_check:
            raise ValidationError(f"沒有足夠的對國家權限")

        if lock:
            country = country.lock()
        self.request.country = country
        return country


class TeamViewMixin:
    def get_team(self, role, lock=False):
        chara = self.get_chara()
        team = chara.team

        if team is None:
            raise ValidationError(f"未加入隊伍")

        if role == 'leader':
            pass_role_check = (team.leader == chara)
        elif role == 'member':
            pass_role_check = True
        else:
            raise Exception("ilegal role setting")

        if not pass_role_check:
            raise ValidationError(f"沒有足夠的對隊伍權限")

        if lock:
            team = team.lock()
        self.request.team = team
        return team


class LockObjectMixin:
    def get_object(self, lock=False):
        """
        copy from drf generic module
        """
        queryset = self.filter_queryset(self.get_queryset())
        if lock:
            queryset = queryset.select_for_update()

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = generics.get_object_or_404(queryset, **filter_kwargs)

        self.check_object_permissions(self.request, obj)

        return obj


class CharaProcessPayloadViewMixin:
    lock_chara = True

    with_instance = False
    lock_instance = False

    def process_payload(self, request):
        chara = self.get_chara(lock=self.lock_chara)
        if self.with_instance:
            serializer = self.get_serializer(self.get_object(lock=self.lock_instance), data=request.data)
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        if result is None:
            return Response({'status': 'success'})
        else:
            return Response(result)


class CharaPostViewMixin(CharaProcessPayloadViewMixin):
    def post(self, request):
        return self.process_payload(request)


class CountryPostViewMixin:
    lock_chara = True
    lock_country = True
    role = 'king'

    def post(self, request):
        chara = self.get_chara(lock=self.lock_chara)
        country = self.get_country(role=self.role, lock=self.lock_country)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        if result is None:
            return Response({'status': 'success'})
        else:
            return Response(result)


class TeamProcessPayloadViewMixin:
    lock_chara = True
    lock_team = True
    role = 'leader'

    with_instance = False
    lock_instance = False

    def process_payload(self, request):
        chara = self.get_chara(lock=self.lock_chara)
        team = self.get_team(role=self.role, lock=self.lock_team)
        if self.with_instance:
            serializer = self.get_serializer(self.get_object(lock=self.lock_instance), data=request.data)
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        if result is None:
            return Response({'status': 'success'})
        else:
            return Response(result)


class TeamPostViewMixin(TeamProcessPayloadViewMixin):
    def post(self, request):
        return self.process_payload(request)


class ListViewMixin:
    def list(self, request, queryset=None, *args, **kwargs):
        if queryset is None:
            queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BaseGenericViewSet(ListViewMixin, LockObjectMixin, TeamViewMixin, CountryViewMixin, CharaViewMixin, viewsets.GenericViewSet):
    filterset_class = None

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_serializer_class()

    def get_queryset(self):
        try:
            return self.action_querysets[self.action].all()
        except (KeyError, AttributeError):
            return super().get_queryset()


class BaseGenericAPIView(ListViewMixin, LockObjectMixin, TeamViewMixin, CountryViewMixin, CharaViewMixin, generics.GenericAPIView):
    filterset_class = None
