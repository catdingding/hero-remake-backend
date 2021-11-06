# Generated by Django 3.2 on 2021-09-18 12:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('item', '0006_equipment_is_locked'),
        ('battle', '0005_alter_battleresult_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='dungeon',
            name='is_infinite',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dungeon',
            name='ticket_cost',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='dungeon',
            name='ticket_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='item.itemtype'),
        ),
    ]