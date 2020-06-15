from base.views import BaseViewSet, BaseGenericAPIView, CharaViewMixin
from rest_framework.response import Response

from country.serializers import FoundCountrySerializer, JoinCountrySerializer, LeaveCountrySerializer


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
