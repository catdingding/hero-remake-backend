# Generated by Django 3.0.6 on 2021-05-23 18:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0004_auto_20210308_1718'),
    ]

    operations = [
        migrations.RenameField(
            model_name='log',
            old_name='type',
            new_name='category',
        ),
    ]