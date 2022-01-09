from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from system.views import LogView
from world.views import MoveView, MapView, ElementTypeView
from user.views import RegistrationView, ChangePasswordView
from chara.views import (
    CharaProfileView, CharaIntroductionView, SendGoldView, SlotEquipView, SlotDivestView, RestView, UserCharaView,
    CharaStorageItemView, CharaViewSet, IncreaseHPMPMaxView, HandInQuestView, ChangeAvatarView, CharaBagItemView,
    PartnerAssignView
)
from ability.views import (
    LearnAbilityView, AvailableToLearnAbilityView, SetAbilityView, AvailableToSetAbilityView, AlchemyOptionViewSet,
    AbilityView
)
from job.views import (
    SetSkillView, AvailableSkillView, AvailableJobView, ChangeJobView, ExerciseView, ExerciseRewardView
)
from item.views import (
    UseItemView, SendItemView, StorageTakeView, StoragePutView, SmithUpgradeView, SmithReplaceAbilityView,
    PetUpgradeView, SmithReplaceElementTypeView, BattleMapTicketToItemView, PetTypeView, ToggleEquipmentLockView,
    ItemTypeView, SmithEquipmentTransformView
)
from country.views import (
    FoundCountryView, LeaveCountryView, ChangeKingView, CountryDismissView,
    CountryItemPutView, CountryItemTakeView, CountryDonateView, CountryItemView,
    CountryViewSet, CountryJoinRequestViewSet, CountryOfficialViewSet,
    CountryOccupyLocationView, CountryAbandonLocationView, CountryBuildTownView,
    CountryUpgradeStorageView, SetCountrySettingView, CountryRenameTownView
)
from team.views import (
    TeamViewSet, FoundTeamView, LeaveTeamView, TeamJoinRequestViewSet, DismissTeamMemberView, DisbandTeamView,
    ChangeTeamDungeonRecordStatusView, ChangeLeaderView
)
from trade.views import (
    AuctionViewSet, SaleViewSet, PurchaseViewSet, ExchangeOptionViewSet, StoreOptionViewSet, SellItemView,
    MemberShopViewSet, LotteryView, BuyLotteryView, ParcelViewSet
)
from battle.views import (
    BattleMapViewSet, PvPFightView, DungeonFightView, BattleResultViewSet, WorldBossFightView, WorldBossView,
    ArenaFightView, ArenaView
)
from town.views import InnSleepView, ChangeNameView
from home.views import CharaFarmExpandView, CharaFarmPlaceItemView, CharaFarmHarvestView, CharaFarmRemoveItemView

router = SimpleRouter()

router.register(r'charas', CharaViewSet)
router.register(r'trade/auctions', AuctionViewSet)
router.register(r'trade/sales', SaleViewSet)
router.register(r'trade/purchases', PurchaseViewSet)
router.register(r'trade/exchange-options', ExchangeOptionViewSet)
router.register(r'trade/parcels', ParcelViewSet)
router.register(r'ability/alchemy-options', AlchemyOptionViewSet)
router.register(r'trade/store-options', StoreOptionViewSet)
router.register(r'battle/battle-maps', BattleMapViewSet)
router.register(r'battle/battle-results', BattleResultViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'country/join-requests', CountryJoinRequestViewSet)
router.register(r'country/officials', CountryOfficialViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'team/join-requests', TeamJoinRequestViewSet)
router.register(r'trade/member-shop', MemberShopViewSet, basename='member-shop')

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
    path('chara/item/toggle-equipment-lock/', ToggleEquipmentLockView.as_view()),
    path('chara/bag/items/', CharaBagItemView.as_view()),
    path('chara/storage/items/', CharaStorageItemView.as_view()),
    path('chara/storage/take/', StorageTakeView.as_view()),
    path('chara/storage/put/', StoragePutView.as_view()),
    path('chara/slot/equip/', SlotEquipView.as_view()),
    path('chara/slot/divest/', SlotDivestView.as_view()),
    path('chara/partner/assign/', PartnerAssignView.as_view()),
    path('chara/farm/expand/', CharaFarmExpandView.as_view()),
    path('chara/farm/place-item/', CharaFarmPlaceItemView.as_view()),
    path('chara/farm/remove-item/', CharaFarmRemoveItemView.as_view()),
    path('chara/farm/harvest/', CharaFarmHarvestView.as_view()),
    path('chara/change-avatar/', ChangeAvatarView.as_view()),
    path('chara/battle-map-ticket-to-item/', BattleMapTicketToItemView.as_view()),
    path('battle/pvp-fight/', PvPFightView.as_view()),
    path('battle/arenas/', ArenaView.as_view()),
    path('battle/arena-fight/', ArenaFightView.as_view()),
    path('battle/dungeon-fight/', DungeonFightView.as_view()),
    path('battle/world-boss-fight/', WorldBossFightView.as_view()),
    path('country/found/', FoundCountryView.as_view()),
    path('country/leave/', LeaveCountryView.as_view()),
    path('country/change-king/', ChangeKingView.as_view()),
    path('country/set-setting/', SetCountrySettingView.as_view()),
    path('country/dismiss/', CountryDismissView.as_view()),
    path('country/storage/items/', CountryItemView.as_view()),
    path('country/storage/take/', CountryItemTakeView.as_view()),
    path('country/storage/put/', CountryItemPutView.as_view()),
    path('country/donate/', CountryDonateView.as_view()),
    path('country/occupy-location/', CountryOccupyLocationView.as_view()),
    path('country/abandon-location/', CountryAbandonLocationView.as_view()),
    path('country/build-town/', CountryBuildTownView.as_view()),
    path('country/rename-town/', CountryRenameTownView.as_view()),
    path('country/upgrade-storage/', CountryUpgradeStorageView.as_view()),
    path('team/found/', FoundTeamView.as_view()),
    path('team/leave/', LeaveTeamView.as_view()),
    path('team/dismiss-member/', DismissTeamMemberView.as_view()),
    path('team/disband/', DisbandTeamView.as_view()),
    path('team/change-leader/', ChangeLeaderView.as_view()),
    path('team/change-dungeon-record-status/', ChangeTeamDungeonRecordStatusView.as_view()),
    path('smith/upgrade/', SmithUpgradeView.as_view()),
    path('smith/replace-ability/', SmithReplaceAbilityView.as_view()),
    path('smith/replace-element-type/', SmithReplaceElementTypeView.as_view()),
    path('smith/transform-quipment/', SmithEquipmentTransformView.as_view()),
    path('pet/upgrade/', PetUpgradeView.as_view()),
    path('map/', MapView.as_view()),
    path('world/element-types/', ElementTypeView.as_view()),
    path('user/charas/', UserCharaView.as_view()),
    path('exercise-rewards/', ExerciseRewardView.as_view()),
    path('abilities/', AbilityView.as_view()),
    path('item/pet-types/', PetTypeView.as_view()),
    path('item/item-types/', ItemTypeView.as_view()),
    path('town/inn/sleep/', InnSleepView.as_view()),
    path('town/change-name/', ChangeNameView.as_view()),
    path('logs/', LogView.as_view()),
    path('trade/lotteries/', LotteryView.as_view()),
    path('trade/lottery/buy/', BuyLotteryView.as_view()),
    path('world-bosses/', WorldBossView.as_view()),
] + router.urls
