from django.utils.timezone import localtime

from rest_framework import viewsets, views, generics, exceptions


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
