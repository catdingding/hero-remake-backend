from base.views import BaseGenericAPIView, CharaPostViewMixin
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.filters import SearchFilter

from system.models import Log
from system.serializers import LogSerializer


class LogView(ListModelMixin, BaseGenericAPIView):
    serializer_class = LogSerializer
    queryset = Log.objects.all()

    filter_backends = [SearchFilter]
    search_fields = ['category', 'content']

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset)[:200]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
