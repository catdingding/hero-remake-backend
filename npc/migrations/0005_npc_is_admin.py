# Generated by Django 4.0 on 2022-03-26 04:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('npc', '0004_npcskillsetting_probability'),
    ]

    operations = [
        migrations.AddField(
            model_name='npc',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
    ]