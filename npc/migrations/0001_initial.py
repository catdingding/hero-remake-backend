# Generated by Django 3.2 on 2022-01-11 16:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('job', '0001_initial'),
        ('world', '0007_locationbufftype_description'),
        ('ability', '0002_auto_20200901_1442'),
    ]

    operations = [
        migrations.CreateModel(
            name='NPC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('hp', models.PositiveIntegerField()),
                ('mp', models.PositiveIntegerField()),
                ('has_image', models.BooleanField()),
                ('abilities', models.ManyToManyField(to='ability.Ability')),
                ('element_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='world.elementtype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NPCSkillSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('hp_percentage', models.PositiveSmallIntegerField()),
                ('mp_percentage', models.PositiveSmallIntegerField()),
                ('defender_hp_percentage', models.PositiveSmallIntegerField(default=100)),
                ('defender_mp_percentage', models.PositiveSmallIntegerField(default=100)),
                ('order', models.IntegerField()),
                ('npc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skill_settings', to='npc.npc')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='job.skill')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NPCMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('category', models.CharField(max_length=20)),
                ('content', models.CharField(max_length=100)),
                ('npc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='npc.npc')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NPCInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('npc', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='info', to='npc.npc')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NPCConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('input_content', models.CharField(max_length=100)),
                ('output_content', models.CharField(max_length=100)),
                ('npc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to='npc.npc')),
            ],
            options={
                'unique_together': {('npc', 'input_content')},
            },
        ),
        migrations.CreateModel(
            name='NPCAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('value', models.IntegerField()),
                ('npc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='npc.npc')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='world.attributetype')),
            ],
            options={
                'unique_together': {('npc', 'type')},
            },
        ),
    ]
