# Generated by Django 4.0 on 2022-04-04 03:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0036_rename_member_point_chara_member_point_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='chara',
            name='member_point_free',
            field=models.PositiveIntegerField(default=0),
        ),
    ]