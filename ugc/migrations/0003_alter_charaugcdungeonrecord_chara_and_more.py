# Generated by Django 4.0 on 2022-02-07 16:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0023_charaachievement_charaachievementcategory_and_more'),
        ('ugc', '0002_charaugcdungeonrecord'),
    ]

    operations = [
        migrations.AlterField(
            model_name='charaugcdungeonrecord',
            name='chara',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ugc_dungeon_records', to='chara.chara'),
        ),
        migrations.AlterField(
            model_name='charaugcdungeonrecord',
            name='dungeon',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chara_records', to='ugc.ugcdungeon'),
        ),
    ]
