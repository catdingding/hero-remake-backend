from base.views import BaseGenericAPIView
from base.parsers import MultipartJsonParser

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from user.serializers import RegistrationSerializer, ChangePasswordSerializer


class RegistrationView(BaseGenericAPIView):
    permission_classes = [AllowAny]
    parser_classes = [MultipartJsonParser]
    serializer_class = RegistrationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)}, status=201)


class ChangePasswordView(BaseGenericAPIView):
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'success'})
