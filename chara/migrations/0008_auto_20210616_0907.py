# Generated by Django 3.0.6 on 2021-06-16 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0007_remove_chararecord_monthly_level_up'),
    ]

    operations = [
        migrations.AddField(
            model_name='chara',
            name='has_auto_heal',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='chara',
            name='has_cold_down_bonus',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='chara',
            name='has_quest_bonus',
            field=models.BooleanField(default=False),
        ),
    ]
