# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-08 01:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ChampionMastery', '0010_auto_20160507_2048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='championmastery',
            name='region',
            field=models.CharField(db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='match',
            name='match_id',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='match',
            name='region',
            field=models.CharField(db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='matchlist',
            name='match_priority',
            field=models.IntegerField(db_index=True, default=1),
        ),
        migrations.AlterField(
            model_name='matchlist',
            name='match_used',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='matchlist',
            name='region',
            field=models.CharField(db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='summoners',
            name='region',
            field=models.CharField(db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='summoners',
            name='summoner_id',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='summoners',
            name='summoner_priority',
            field=models.IntegerField(db_index=True, default=1),
        ),
        migrations.AlterField(
            model_name='summoners',
            name='summoner_used',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
