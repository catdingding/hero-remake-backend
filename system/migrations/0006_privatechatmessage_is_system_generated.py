# Generated by Django 3.0.6 on 2021-06-30 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0005_auto_20210523_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='privatechatmessage',
            name='is_system_generated',
            field=models.BooleanField(default=False),
        ),
    ]
