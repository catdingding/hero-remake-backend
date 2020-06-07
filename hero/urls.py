from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from world.views import MoveView, MapView
from user.views import RegistrationView, ChangePasswordView
from chara.views import CharaIntroductionView, SendMoneyView
from ability.views import LearnAbilityView, AvailableToLearnAbilityView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/registration/', RegistrationView.as_view()),
    path('user/change-password/', ChangePasswordView.as_view()),
    path('chara/<int:chara_id>/introduction/', CharaIntroductionView.as_view()),
    path('chara/<int:chara_id>/move/', MoveView.as_view()),
    path('chara/<int:chara_id>/send-money/', SendMoneyView.as_view()),
    path('chara/<int:chara_id>/ability/learn/', LearnAbilityView.as_view()),
    path('chara/<int:chara_id>/ability/available-to-learn/', AvailableToLearnAbilityView.as_view()),
    path('map/', MapView.as_view())
]
