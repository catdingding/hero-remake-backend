# Generated by Django 4.0 on 2022-06-04 12:06

from django.db import migrations, models
import django.db.models.deletion


def create_chara_home(apps, schema_editor):
    Chara = apps.get_model('chara', 'Chara')
    CharaHome = apps.get_model('chara', 'CharaHome')
    for chara in Chara.objects.all():
        CharaHome.objects.create(chara=chara, chars=[''] * 900)


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0038_characonfig_use_image_background'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharaHome',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('chars', models.JSONField()),
                ('chara', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='home', to='chara.chara')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RunPython(create_chara_home)
    ]