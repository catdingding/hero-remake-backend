# Generated by Django 3.2 on 2021-07-15 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('battle', '0004_battleresult_dungeon_dungeonfloor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='battleresult',
            name='content',
            field=models.JSONField(),
        ),
    ]