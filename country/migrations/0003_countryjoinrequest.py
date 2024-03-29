# Generated by Django 3.0.6 on 2021-01-23 07:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0002_auto_20200901_1442'),
        ('country', '0002_auto_20210119_1007'),
    ]

    operations = [
        migrations.CreateModel(
            name='CountryJoinRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('chara', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='country_join_requests', to='chara.Chara')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='country_join_requests', to='country.Country')),
            ],
            options={
                'unique_together': {('country', 'chara')},
            },
        ),
    ]
