from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from world.views import MoveView, MapView
from user.views import RegistrationView, ChangePasswordView
from chara.views import CharaIntroductionView, SendMoneyView, SlotEquipView, SlotDivestView
from ability.views import LearnAbilityView, AvailableToLearnAbilityView, SetAbilityView, AvailableToSetAbilityView
from job.views import SetSkillView, AvailableSkillView, AvailableJobView, ChangeJobView
from item.views import UseItemView, SendItemView, StorageTakeView, StoragePutView
from country.views import (
    FoundCountryView, JoinCountryView, LeaveCountryView, ChangeKingView, CountryDismissView, SetOfficialsView,
    CountryItemPutView, CountryItemTakeView, CountryDonateView
)

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
    path('chara/<int:chara_id>/ability/set/', SetAbilityView.as_view()),
    path('chara/<int:chara_id>/ability/available-to-set/', AvailableToSetAbilityView.as_view()),
    path('chara/<int:chara_id>/skill/set/', SetSkillView.as_view()),
    path('chara/<int:chara_id>/skill/available/', AvailableSkillView.as_view()),
    path('chara/<int:chara_id>/job/change/', ChangeJobView.as_view()),
    path('chara/<int:chara_id>/job/available/', AvailableJobView.as_view()),
    path('chara/<int:chara_id>/item/use/', UseItemView.as_view()),
    path('chara/<int:chara_id>/item/send/', SendItemView.as_view()),
    path('chara/<int:chara_id>/storage/take/', StorageTakeView.as_view()),
    path('chara/<int:chara_id>/storage/put/', StoragePutView.as_view()),
    path('chara/<int:chara_id>/slot/equip/', SlotEquipView.as_view()),
    path('chara/<int:chara_id>/slot/divest/', SlotDivestView.as_view()),
    path('chara/<int:chara_id>/country/found/', FoundCountryView.as_view()),
    path('chara/<int:chara_id>/country/join/', JoinCountryView.as_view()),
    path('chara/<int:chara_id>/country/leave/', LeaveCountryView.as_view()),
    path('chara/<int:chara_id>/country/change-king/', ChangeKingView.as_view()),
    path('chara/<int:chara_id>/country/dismiss/', CountryDismissView.as_view()),
    path('chara/<int:chara_id>/country/set-officials/', SetOfficialsView.as_view()),
    path('chara/<int:chara_id>/country/item/take/', CountryItemTakeView.as_view()),
    path('chara/<int:chara_id>/country/item/put/', CountryItemPutView.as_view()),
    path('chara/<int:chara_id>/country/donate/', CountryDonateView.as_view()),
    path('map/', MapView.as_view())
]
