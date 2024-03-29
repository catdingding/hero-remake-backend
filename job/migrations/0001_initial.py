# Generated by Django 3.0.6 on 2020-09-01 14:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('world', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('rank', models.PositiveSmallIntegerField()),
                ('base_hp', models.IntegerField(default=0)),
                ('base_mp', models.IntegerField(default=0)),
                ('description', models.CharField(max_length=100)),
                ('attribute_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='world.AttributeType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SkillType',
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
            name='Skill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('rank', models.IntegerField(null=True)),
                ('is_general', models.BooleanField(default=False)),
                ('power', models.IntegerField()),
                ('rate', models.IntegerField()),
                ('mp_cost', models.IntegerField()),
                ('action_cost', models.IntegerField()),
                ('attribute_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='world.AttributeType')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='job.SkillType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExerciseReward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('limit_growth', models.IntegerField()),
                ('job_attribute_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='exercise_rewards', to='world.AttributeType')),
                ('reward_attribute_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='world.AttributeType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='JobAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('base_value', models.IntegerField(default=0)),
                ('require_value', models.IntegerField(default=0)),
                ('require_proficiency', models.IntegerField(default=0)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='job.Job')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='world.AttributeType')),
            ],
            options={
                'unique_together': {('job', 'type')},
            },
        ),
    ]
