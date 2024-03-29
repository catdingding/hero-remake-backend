# Generated by Django 3.0.6 on 2020-09-01 14:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('battle', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('en_name', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=10, unique=True)),
                ('class_name', models.CharField(max_length=10, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ElementType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('en_name', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=10, unique=True)),
                ('suppressed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='world.ElementType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('chaos_score', models.PositiveIntegerField()),
                ('battle_map', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='battle.BattleMap')),
                ('element_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='world.ElementType')),
            ],
            options={
                'unique_together': {('x', 'y')},
            },
        ),
        migrations.CreateModel(
            name='LocationBuffType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('is_positive', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SlotType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('en_name', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=10, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LocationBuff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('value', models.IntegerField(null=True)),
                ('due_date', models.DateTimeField(null=True)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.Location')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='world.LocationBuffType')),
            ],
            options={
                'unique_together': {('location', 'type')},
            },
        ),
    ]
