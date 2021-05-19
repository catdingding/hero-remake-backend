# Generated by Django 3.0.6 on 2020-09-01 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('world', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attributetype',
            name='en_name',
            field=models.CharField(max_length=10, unique=True),
        ),
        migrations.AlterField(
            model_name='elementtype',
            name='en_name',
            field=models.CharField(max_length=10, unique=True),
        ),
        migrations.AlterField(
            model_name='slottype',
            name='en_name',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]