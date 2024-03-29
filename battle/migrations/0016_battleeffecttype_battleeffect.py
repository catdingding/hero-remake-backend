# Generated by Django 4.0 on 2022-04-22 07:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('battle', '0015_monsterskillsetting_probability_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BattleEffectType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=20, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BattleEffect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('value', models.DecimalField(decimal_places=4, max_digits=8)),
                ('description', models.CharField(max_length=100)),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='battle.battleeffecttype')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
