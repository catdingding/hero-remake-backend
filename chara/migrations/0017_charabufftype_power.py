# Generated by Django 3.2 on 2021-12-09 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0016_auto_20211209_1342'),
    ]

    operations = [
        migrations.AddField(
            model_name='charabufftype',
            name='power',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
