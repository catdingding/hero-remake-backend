from django.db.models import Subquery, Q, F

from chara.models import CharaAchievement, CharaAchievementCounter, CharaAchievementType, CharaTitle

from system.utils import send_info_message, send_system_message


def update_achievement_counter(chara, category_id, value, mode):
    assert mode in ['set', 'increase']
    if mode == 'set':
        affected_rows = CharaAchievementCounter.objects.filter(chara=chara.id, category=category_id).update(value=value)
    elif mode == 'increase':
        affected_rows = CharaAchievementCounter.objects.filter(
            chara=chara.id, category=category_id).update(value=F('value') + value)

    if affected_rows == 0:
        CharaAchievementCounter.objects.create(chara=chara, category_id=category_id, value=value)

    return obtain_achievement(chara, category_id)


def obtain_achievement(chara, category_id):
    achivement_types = CharaAchievementType.objects.filter(
        ~Q(id__in=Subquery(CharaAchievement.objects.filter(chara=chara, type__category=category_id).values('type'))),
        category=category_id,
        requirement__lte=Subquery(
            CharaAchievementCounter.objects.filter(chara=chara, category=category_id).values('value')[:1]
        )
    ).select_related('title_type')

    if achivement_types:
        CharaAchievement.objects.bulk_create([
            CharaAchievement(chara=chara, type=achivement_type)
            for achivement_type in achivement_types
        ])
        CharaTitle.objects.bulk_create([
            CharaTitle(chara=chara, type=achivement_type.title_type)
            for achivement_type in achivement_types
            if achivement_type.title_type
        ], ignore_conflicts=True)

        for achivement_type in achivement_types:
            message = f"達成了「{achivement_type.name}」成就"
            if achivement_type.title_type:
                message += f"，獲得了「{achivement_type.title_type.name}」稱號"
            send_info_message(chara.id, "success", message)

            if achivement_type.need_announce:
                send_system_message("系統醬", 1, f"恭喜{chara.name}達成了『{achivement_type.name}』成就~")

    return achivement_types
