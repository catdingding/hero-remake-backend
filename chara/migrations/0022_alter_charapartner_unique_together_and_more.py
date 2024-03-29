# Generated by Django 4.0 on 2022-01-16 06:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('npc', '0001_initial'),
        ('battle', '0013_arena'),
        ('chara', '0021_auto_20220109_0735'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='charapartner',
            unique_together={('chara', 'target_monster'), ('chara', 'target_chara')},
        ),
        migrations.AddField(
            model_name='charapartner',
            name='target_npc',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='npc.npc'),
        ),
        migrations.AlterUniqueTogether(
            name='charapartner',
            unique_together={('chara', 'target_monster'), ('chara', 'target_npc'), ('chara', 'target_chara')},
        ),
    ]
