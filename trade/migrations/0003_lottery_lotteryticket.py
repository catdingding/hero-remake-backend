# Generated by Django 3.2 on 2021-09-23 15:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chara', '0014_auto_20210922_1226'),
        ('trade', '0002_auto_20210829_2013'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lottery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('nth', models.IntegerField()),
                ('price', models.BigIntegerField()),
                ('number_min', models.IntegerField()),
                ('number_max', models.IntegerField()),
                ('chara_ticket_limit', models.IntegerField()),
                ('gold', models.BigIntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LotteryTicket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('nth', models.IntegerField()),
                ('number', models.IntegerField()),
                ('chara', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chara.chara')),
                ('lottery', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='trade.lottery')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]