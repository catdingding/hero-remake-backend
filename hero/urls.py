from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from user.views import RegistrationView, ChangePasswordView
from chara.views import CharaIntroductionView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/registration/', RegistrationView.as_view()),
    path('user/change-password/', ChangePasswordView.as_view()),
    path('chara/<int:chara_id>/introduction/', CharaIntroductionView.as_view())
]
