from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin, CountryViewMixin
from rest_framework.response import Response

from country.serializers import (
    FoundCountrySerializer, JoinCountrySerializer, LeaveCountrySerializer,
    CountryDismissSerializer, ChangeKingSerializer, SetOfficialsSerializer
)


class FoundCountryView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = FoundCountrySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class JoinCountryView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = JoinCountrySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class LeaveCountryView(CharaViewMixin, BaseGenericAPIView):
    serializer_class = LeaveCountrySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CountryDismissView(CountryViewMixin, BaseGenericAPIView):
    serializer_class = CountryDismissSerializer

    def post(self, request, country_id):
        country = self.get_country(role='official', lock=True)
        serializer = self.get_serializer(country, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class ChangeKingView(CountryViewMixin, BaseGenericAPIView):
    serializer_class = ChangeKingSerializer

    def post(self, request, country_id):
        country = self.get_country(role='king', lock=True)
        serializer = self.get_serializer(country, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class SetOfficialsView(CountryViewMixin, BaseGenericAPIView):
    serializer_class = SetOfficialsSerializer

    def post(self, request, country_id):
        country = self.get_country(role='king', lock=True)
        serializer = self.get_serializer(country, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})
