from base.views import BaseViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from user.serializers import RegistrationSerializer


class UserViewSet(BaseViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def registration(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token), }, status=201)
