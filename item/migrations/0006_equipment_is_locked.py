# Generated by Django 3.2 on 2021-09-07 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('item', '0005_itemtype_is_transferable'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipment',
            name='is_locked',
            field=models.BooleanField(default=False),
        ),
    ]
