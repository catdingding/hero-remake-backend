# Generated by Django 3.2 on 2022-01-08 13:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('item', '0007_auto_20211114_1205'),
        ('chara', '0019_charafarm'),
    ]

    operations = [
        migrations.AlterField(
            model_name='charaslot',
            name='item',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='item.item', unique=True),
        ),
    ]
