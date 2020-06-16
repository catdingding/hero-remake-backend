from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin, CountryViewMixin
from rest_framework.response import Response

from country.serializers import (
    FoundCountrySerializer, JoinCountrySerializer, LeaveCountrySerializer,
    CountryDismissSerializer, ChangeKingSerializer, SetOfficialsSerializer,
    CountryItemTakeSerializer, CountryItemPutSerializer, CountryDonateSerializer
)


class FoundCountryView(BaseGenericAPIView):
    serializer_class = FoundCountrySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class JoinCountryView(BaseGenericAPIView):
    serializer_class = JoinCountrySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class LeaveCountryView(BaseGenericAPIView):
    serializer_class = LeaveCountrySerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CountryDismissView(BaseGenericAPIView):
    serializer_class = CountryDismissSerializer

    def post(self, request, chara_id):
        country = self.get_country(role='official', lock=True)
        serializer = self.get_serializer(country, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class ChangeKingView(BaseGenericAPIView):
    serializer_class = ChangeKingSerializer

    def post(self, request, chara_id):
        country = self.get_country(role='king', lock=True)
        serializer = self.get_serializer(country, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class SetOfficialsView(BaseGenericAPIView):
    serializer_class = SetOfficialsSerializer

    def post(self, request, chara_id):
        country = self.get_country(role='king', lock=True)
        serializer = self.get_serializer(country, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CountryItemTakeView(BaseGenericAPIView):
    serializer_class = CountryItemTakeSerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        country = self.get_country(role='official', lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CountryItemPutView(BaseGenericAPIView):
    serializer_class = CountryItemPutSerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        country = self.get_country(role='citizen', lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CountryDonateView(BaseGenericAPIView):
    serializer_class = CountryDonateSerializer

    def post(self, request, chara_id):
        chara = self.get_chara(lock=True)
        country = self.get_country(role='citizen', lock=True)
        serializer = self.get_serializer(chara, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})
