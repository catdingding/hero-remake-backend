from base.serializers import SerpyModelSerializer
from battle.models import BattleEffect


class BattleEffectSerializer(SerpyModelSerializer):
    class Meta:
        model = BattleEffect
        fields = ['id', 'name']
