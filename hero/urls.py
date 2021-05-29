from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from system.views import LogView
from world.views import MoveView, MapView, ElementTypeView
from user.views import RegistrationView, ChangePasswordView
from chara.views import (
    CharaProfileView, CharaIntroductionView, SendGoldView, SlotEquipView, SlotDivestView, RestView, UserCharaView,
    CharaStorageItemView, CharaViewSet, IncreaseHPMPMaxView, HandInQuestView
)
from ability.views import (
    LearnAbilityView, AvailableToLearnAbilityView, SetAbilityView, AvailableToSetAbilityView, AlchemyOptionViewSet,
)
from job.views import (
    SetSkillView, AvailableSkillView, AvailableJobView, ChangeJobView, ExerciseView, ExerciseRewardView
)
from item.views import (
    UseItemView, SendItemView, StorageTakeView, StoragePutView, SmithUpgradeView, SmithReplaceAbilityView,
    PetUpgradeView
)
from country.views import (
    FoundCountryView, LeaveCountryView, ChangeKingView, CountryDismissView,
    CountryItemPutView, CountryItemTakeView, CountryDonateView, CountryItemView,
    CountryViewSet, CountryJoinRequestViewSet, CountryOfficialViewSet,
    CountryOccupyLocationView, CountryAbandonLocationView
)
from trade.views import (
    AuctionViewSet, SaleViewSet, PurchaseViewSet, ExchangeOptionViewSet, StoreOptionViewSet, SellItemView
)
from battle.views import BattleMapViewSet, PvPFightView
from town.views import InnSleepView

router = SimpleRouter()

router.register(r'charas', CharaViewSet)
router.register(r'trade/auctions', AuctionViewSet)
router.register(r'trade/sales', SaleViewSet)
router.register(r'trade/purchases', PurchaseViewSet)
router.register(r'trade/exchange-options', ExchangeOptionViewSet)
router.register(r'ability/alchemy-options', AlchemyOptionViewSet)
router.register(r'trade/store-options', StoreOptionViewSet)
router.register(r'battle/battle-maps', BattleMapViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'country/join-requests', CountryJoinRequestViewSet)
router.register(r'country/officials', CountryOfficialViewSet)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/registration/', RegistrationView.as_view()),
    path('user/change-password/', ChangePasswordView.as_view()),
    path('chara/profile/', CharaProfileView.as_view()),
    path('chara/introduction/', CharaIntroductionView.as_view()),
    path('chara/rest/', RestView.as_view()),
    path('chara/move/', MoveView.as_view()),
    path('chara/send-gold/', SendGoldView.as_view()),
    path('chara/ability/learn/', LearnAbilityView.as_view()),
    path('chara/ability/available-to-learn/', AvailableToLearnAbilityView.as_view()),
    path('chara/ability/set/', SetAbilityView.as_view()),
    path('chara/ability/available-to-set/', AvailableToSetAbilityView.as_view()),
    path('chara/skill/set/', SetSkillView.as_view()),
    path('chara/skill/available/', AvailableSkillView.as_view()),
    path('chara/job/change/', ChangeJobView.as_view()),
    path('chara/job/available/', AvailableJobView.as_view()),
    path('chara/exercise/', ExerciseView.as_view()),
    path('chara/increase-hp-mp-max/', IncreaseHPMPMaxView.as_view()),
    path('chara/quest/hand-in/', HandInQuestView.as_view()),
    path('chara/item/use/', UseItemView.as_view()),
    path('chara/item/send/', SendItemView.as_view()),
    path('chara/item/sell/', SellItemView.as_view()),
    path('chara/storage/items/', CharaStorageItemView.as_view()),
    path('chara/storage/take/', StorageTakeView.as_view()),
    path('chara/storage/put/', StoragePutView.as_view()),
    path('chara/slot/equip/', SlotEquipView.as_view()),
    path('chara/slot/divest/', SlotDivestView.as_view()),
    path('battle/pvp-fight/', PvPFightView.as_view()),
    path('country/found/', FoundCountryView.as_view()),
    path('country/leave/', LeaveCountryView.as_view()),
    path('country/change-king/', ChangeKingView.as_view()),
    path('country/dismiss/', CountryDismissView.as_view()),
    path('country/storage/items/', CountryItemView.as_view()),
    path('country/storage/take/', CountryItemTakeView.as_view()),
    path('country/storage/put/', CountryItemPutView.as_view()),
    path('country/donate/', CountryDonateView.as_view()),
    path('country/occupy-location/', CountryOccupyLocationView.as_view()),
    path('country/abandon-location/', CountryAbandonLocationView.as_view()),
    path('smith/upgrade/', SmithUpgradeView.as_view()),
    path('smith/replace-ability/', SmithReplaceAbilityView.as_view()),
    path('pet/upgrade/', PetUpgradeView.as_view()),
    path('map/', MapView.as_view()),
    path('world/element-types/', ElementTypeView.as_view()),
    path('user/charas/', UserCharaView.as_view()),
    path('exercise-rewards/', ExerciseRewardView.as_view()),
    path('town/inn/sleep/', InnSleepView.as_view()),
    path('logs/', LogView.as_view()),
] + router.urls
