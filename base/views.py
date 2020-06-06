from rest_framework import viewsets, views, generics, exceptions


class BaseViewSet(viewsets.ViewSet):
    pass


class BaseGenericAPIView(generics.GenericAPIView):
    pass


class CharaViewMixin:
    def get_chara(self):
        chara = self.request.user.charas.filter(id=self.kwargs.pop('chara_id')).first()
        if chara is None:
            raise exceptions.PermissionDenied("角色錯誤")
        return chara
