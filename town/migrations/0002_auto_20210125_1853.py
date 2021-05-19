# Generated by Django 3.0.6 on 2021-01-25 18:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('country', '0004_auto_20210125_1853'),
        ('town', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='town',
            name='country',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='towns', to='country.Country'),
        ),
    ]