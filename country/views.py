from django.db.models import Count

from base.views import BaseGenericAPIView, BaseGenericViewSet, CharaPostViewMixin, CountryPostViewMixin
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, DestroyModelMixin, CreateModelMixin
from django_filters.rest_framework import DjangoFilterBackend

from country.models import Country, CountryOfficial, CountryJoinRequest
from country.serializers import (
    FoundCountrySerializer, LeaveCountrySerializer,
    CountryDismissSerializer, ChangeKingSerializer,
    CountryItemTakeSerializer, CountryItemPutSerializer, CountryDonateSerializer,
    CountryOfficialSerializer, CountryProfileSerializer,
    CountryJoinRequestSerializer, CountryJoinRequestCreateSerializer, CountryJoinRequestApproveSerializer,
    CountryOccupyLocationSerializer, CountryAbandonLocationSerializer
)
from item.serializers import ItemSerializer


class CountryViewSet(ListModelMixin, RetrieveModelMixin, BaseGenericViewSet):
    serializer_class = CountryProfileSerializer
    queryset = Country.objects.annotate(location_count=Count('locations')).select_related('king').all()


class FoundCountryView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = FoundCountrySerializer


class LeaveCountryView(CharaPostViewMixin, BaseGenericAPIView):
    serializer_class = LeaveCountrySerializer


class CountryJoinRequestViewSet(BaseGenericViewSet):
    queryset = CountryJoinRequest.objects.all()
    serializer_class = CountryJoinRequestSerializer
    serializer_action_classes = {
        'create': CountryJoinRequestCreateSerializer,
        'approve': CountryJoinRequestApproveSerializer,
    }

    def create(self, request):
        chara = self.get_chara(lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'display_message': '入國申請已發送'})

    def list(self, request):
        country = self.get_country(role='official')
        queryset = self.get_queryset().filter(country=country)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def approve(self, request, pk):
        country = self.get_country(role='official', lock=True)
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'display_message': '入國申請已通過'})


class CountryDismissView(BaseGenericAPIView):
    serializer_class = CountryDismissSerializer

    def post(self, request):
        country = self.get_country(role='official', lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class ChangeKingView(BaseGenericAPIView):
    serializer_class = ChangeKingSerializer

    def post(self, request):
        country = self.get_country(role='king', lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CountryOfficialViewSet(CreateModelMixin, ListModelMixin, DestroyModelMixin, BaseGenericViewSet):
    serializer_class = CountryOfficialSerializer
    queryset = CountryOfficial.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['country']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'delete':
            queryset = queryset.filter(country=self.get_country(role='king'))
        return queryset

    def create(self, request):
        country = self.get_country(role='king')
        return super().create(request)

    def destroy(self, request, pk):
        country = self.get_country(role='king')
        return super().destroy(request, pk)


class CountryItemView(BaseGenericAPIView):
    serializer_class = ItemSerializer

    def get(self, request):
        country = self.get_country(role='citizen')
        serializer = self.get_serializer(country.items.all(), many=True)

        return Response(serializer.data)


class CountryItemTakeView(BaseGenericAPIView):
    serializer_class = CountryItemTakeSerializer

    def post(self, request):
        chara = self.get_chara(lock=True)
        country = self.get_country(role='official', lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CountryItemPutView(BaseGenericAPIView):
    serializer_class = CountryItemPutSerializer

    def post(self, request):
        chara = self.get_chara(lock=True)
        country = self.get_country(role='citizen', lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CountryDonateView(BaseGenericAPIView):
    serializer_class = CountryDonateSerializer

    def post(self, request):
        chara = self.get_chara(lock=True)
        country = self.get_country(role='citizen', lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})


class CountryOccupyLocationView(CountryPostViewMixin, BaseGenericAPIView):
    serializer_class = CountryOccupyLocationSerializer


class CountryAbandonLocationView(CountryPostViewMixin, BaseGenericAPIView):
    serializer_class = CountryAbandonLocationSerializer
