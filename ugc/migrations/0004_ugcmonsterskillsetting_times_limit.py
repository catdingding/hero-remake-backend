# Generated by Django 4.0 on 2022-02-17 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ugc', '0003_alter_charaugcdungeonrecord_chara_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ugcmonsterskillsetting',
            name='times_limit',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
