# Generated by Django 3.2 on 2021-08-24 03:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('item', '0004_auto_20210131_1324'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemtype',
            name='is_transferable',
            field=models.BooleanField(default=True),
        ),
    ]
