# Generated by Django 3.0.6 on 2021-01-19 10:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0002_auto_20200901_1442'),
        ('country', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='country',
            name='king',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='king_of', to='chara.Chara'),
        ),
    ]
