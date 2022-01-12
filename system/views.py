from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.filters import SearchFilter

from system.models import Log, ChangeLog
from system.serializers import LogSerializer, ChangeLogSerializer


class ChangeLogView(ListModelMixin, BaseGenericAPIView):
    serializer_class = ChangeLogSerializer
    queryset = ChangeLog.objects.all().order_by('-time')

    filter_backends = [SearchFilter]
    search_fields = ['category', 'content']

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class LogView(ListModelMixin, BaseGenericAPIView):
    serializer_class = LogSerializer
    queryset = Log.objects.all()

    filter_backends = [SearchFilter]
    search_fields = ['category', 'content']

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).order_by('-created_at')[:200]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
