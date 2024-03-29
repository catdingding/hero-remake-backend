# Generated by Django 3.0.6 on 2021-03-08 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0002_auto_20210308_1659'),
    ]

    operations = [
        migrations.RenameField(
            model_name='countrychatmessage',
            old_name='chara',
            new_name='sender',
        ),
        migrations.RenameField(
            model_name='publicchatmessage',
            old_name='chara',
            new_name='sender',
        ),
        migrations.RemoveField(
            model_name='countrychatmessage',
            name='message',
        ),
        migrations.RemoveField(
            model_name='log',
            name='message',
        ),
        migrations.RemoveField(
            model_name='privatechatmessage',
            name='message',
        ),
        migrations.RemoveField(
            model_name='publicchatmessage',
            name='message',
        ),
        migrations.AddField(
            model_name='countrychatmessage',
            name='content',
            field=models.CharField(default='', max_length=400),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='log',
            name='content',
            field=models.CharField(default='', max_length=400),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='privatechatmessage',
            name='content',
            field=models.CharField(default='', max_length=400),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='publicchatmessage',
            name='content',
            field=models.CharField(default='', max_length=400),
            preserve_default=False,
        ),
    ]
