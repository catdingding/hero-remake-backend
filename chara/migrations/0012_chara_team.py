# Generated by Django 3.0.6 on 2021-07-11 09:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0001_initial'),
        ('chara', '0011_chara_avatar_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='chara',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='members', to='team.Team'),
        ),
    ]
