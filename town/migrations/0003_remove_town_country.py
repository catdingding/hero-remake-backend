# Generated by Django 3.0.6 on 2021-05-27 07:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('town', '0002_auto_20210125_1853'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='town',
            name='country',
        ),
    ]
