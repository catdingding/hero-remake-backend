# Generated by Django 3.2 on 2021-09-22 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0013_chara_has_transfer_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='charaskillsetting',
            name='defender_hp_percentage',
            field=models.PositiveSmallIntegerField(default=100),
        ),
        migrations.AddField(
            model_name='charaskillsetting',
            name='defender_mp_percentage',
            field=models.PositiveSmallIntegerField(default=100),
        ),
    ]
