from django.db.models import Subquery, Q, F

from chara.models import CharaAchievement, CharaAchievementCounter, CharaAchievementType, CharaTitle

from system.utils import send_info_message


def update_achievement_counter(chara_id, category_id, value, mode):
    assert mode in ['set', 'increase']
    if mode == 'set':
        affected_rows = CharaAchievementCounter.objects.filter(chara=chara_id, category=category_id).update(value=value)
    elif mode == 'increase':
        affected_rows = CharaAchievementCounter.objects.filter(
            chara=chara_id, category=category_id).update(value=F('value') + value)

    if affected_rows == 0:
        CharaAchievementCounter.objects.create(chara_id=chara_id, category_id=category_id, value=value)

    return obtain_achievement(chara_id, category_id)


def obtain_achievement(chara_id, category_id):
    achivement_types = CharaAchievementType.objects.filter(
        ~Q(id__in=Subquery(CharaAchievement.objects.filter(chara=chara_id, type__category=category_id).values('type'))),
        category=category_id,
        requirement__lte=Subquery(
            CharaAchievementCounter.objects.filter(chara=chara_id, category=category_id).values('value')[:1]
        )
    ).select_related('title_type')

    if achivement_types:
        CharaAchievement.objects.bulk_create([
            CharaAchievement(chara_id=chara_id, type=achivement_type)
            for achivement_type in achivement_types
        ])
        CharaTitle.objects.bulk_create([
            CharaTitle(chara_id=chara_id, type=achivement_type.title_type)
            for achivement_type in achivement_types
            if achivement_type.title_type
        ], ignore_conflicts=True)

        for achivement_type in achivement_types:
            message = f"獲得了「{achivement_type.name}」成就"
            if achivement_type.title_type:
                message += f"，獲得了「{achivement_type.title_type.name}」稱號"
            send_info_message(chara_id, "success", message)

    return achivement_types
