# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-09 21:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ChampionMastery', '0012_auto_20160507_2138'),
    ]

    operations = [
        migrations.AddField(
            model_name='champions',
            name='image_name',
            field=models.CharField(default='a', max_length=256),
            preserve_default=False,
        ),
    ]
