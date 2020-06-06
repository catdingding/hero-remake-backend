from rest_framework import viewsets, views, generics, exceptions


class BaseViewSet(viewsets.ViewSet):
    pass


class BaseGenericAPIView(generics.GenericAPIView):
    pass


class CharaViewMixin:
    def get_chara(self, lock=False):
        queryset = self.request.user.charas.filter(id=self.kwargs['chara_id'])
        if lock:
            queryset = queryset.select_for_update()

        chara = queryset.first()
        if chara is None:
            raise exceptions.PermissionDenied("角色錯誤")
        return chara
