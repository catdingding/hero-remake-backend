# Generated by Django 3.2 on 2021-10-03 14:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('item', '0006_equipment_is_locked'),
        ('trade', '0004_auto_20211003_1113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='item',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='item.item'),
        ),
    ]