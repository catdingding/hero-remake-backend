from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from world.views import MoveView, MapView
from user.views import RegistrationView, ChangePasswordView
from chara.views import CharaIntroductionView, SendMoneyView, SlotEquipView, SlotDivestView, RestView
from ability.views import (
    LearnAbilityView, AvailableToLearnAbilityView, SetAbilityView, AvailableToSetAbilityView, AlchemyOptionViewSet
)
from job.views import SetSkillView, AvailableSkillView, AvailableJobView, ChangeJobView, ExerciseView
from item.views import UseItemView, SendItemView, StorageTakeView, StoragePutView
from country.views import (
    FoundCountryView, JoinCountryView, LeaveCountryView, ChangeKingView, CountryDismissView, SetOfficialsView,
    CountryItemPutView, CountryItemTakeView, CountryDonateView
)
from trade.views import AuctionViewSet, SaleViewSet, PurchaseViewSet, ExchangeOptionViewSet, StoreOptionViewSet
from battle.views import BattleMapViewSet

router = SimpleRouter()

router.register(r'trade/auctions', AuctionViewSet)
router.register(r'trade/sales', SaleViewSet)
router.register(r'trade/purchases', PurchaseViewSet)
router.register(r'trade/exchange-options', ExchangeOptionViewSet)
router.register(r'chara/alchemy-options', AlchemyOptionViewSet)
router.register(r'trade/store-options', StoreOptionViewSet)
router.register(r'battle/battle-maps', BattleMapViewSet)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/registration/', RegistrationView.as_view()),
    path('user/change-password/', ChangePasswordView.as_view()),
    path('chara/introduction/', CharaIntroductionView.as_view()),
    path('chara/rest/', RestView.as_view()),
    path('chara/move/', MoveView.as_view()),
    path('chara/send-money/', SendMoneyView.as_view()),
    path('chara/ability/learn/', LearnAbilityView.as_view()),
    path('chara/ability/available-to-learn/', AvailableToLearnAbilityView.as_view()),
    path('chara/ability/set/', SetAbilityView.as_view()),
    path('chara/ability/available-to-set/', AvailableToSetAbilityView.as_view()),
    path('chara/skill/set/', SetSkillView.as_view()),
    path('chara/skill/available/', AvailableSkillView.as_view()),
    path('chara/job/change/', ChangeJobView.as_view()),
    path('chara/job/available/', AvailableJobView.as_view()),
    path('chara/exercise/', ExerciseView.as_view()),
    path('chara/item/use/', UseItemView.as_view()),
    path('chara/item/send/', SendItemView.as_view()),
    path('chara/storage/take/', StorageTakeView.as_view()),
    path('chara/storage/put/', StoragePutView.as_view()),
    path('chara/slot/equip/', SlotEquipView.as_view()),
    path('chara/slot/divest/', SlotDivestView.as_view()),
    path('country/found/', FoundCountryView.as_view()),
    path('country/join/', JoinCountryView.as_view()),
    path('country/leave/', LeaveCountryView.as_view()),
    path('country/change-king/', ChangeKingView.as_view()),
    path('country/dismiss/', CountryDismissView.as_view()),
    path('country/set-officials/', SetOfficialsView.as_view()),
    path('country/item/take/', CountryItemTakeView.as_view()),
    path('country/item/put/', CountryItemPutView.as_view()),
    path('country/donate/', CountryDonateView.as_view()),
    path('map/', MapView.as_view())
] + router.urls
