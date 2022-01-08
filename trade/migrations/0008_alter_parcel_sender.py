# Generated by Django 3.2 on 2022-01-01 09:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0019_charafarm'),
        ('trade', '0007_exchangeoption_store_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parcel',
            name='sender',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sent_parcels', to='chara.chara'),
        ),
    ]