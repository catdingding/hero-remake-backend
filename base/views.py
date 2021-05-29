from django.db.models import Q, Exists, OuterRef
from django.utils.timezone import localtime

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
            if waiting_time > 0:
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


class CharaPostViewMixin:
    LOCK_CHARA = True

    def post(self, request):
        chara = self.get_chara(lock=self.LOCK_CHARA)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        if result is None:
            return Response({'status': 'success'})
        else:
            return Response(result)


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


class SerializerFieldsMixin:
    serializer_fields = None

    def get_serializer(self, *args, **kwargs):
        if 'fields' not in kwargs and self.serializer_fields is not None:
            kwargs['fields'] = self.serializer_fields

        return super().get_serializer(*args, **kwargs)


class BaseGenericViewSet(SerializerFieldsMixin, LockObjectMixin, CountryViewMixin, CharaViewMixin, viewsets.GenericViewSet):
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


class BaseGenericAPIView(SerializerFieldsMixin, LockObjectMixin, CountryViewMixin, CharaViewMixin, generics.GenericAPIView):
    pass
