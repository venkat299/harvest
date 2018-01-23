# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-22 15:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('harvest', '0002_watchlist_percent_low'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ndaylow',
            name='allocation',
        ),
        migrations.RemoveField(
            model_name='ndaylow',
            name='strategy',
        ),
        migrations.AddField(
            model_name='watchlist',
            name='allocation',
            field=models.DecimalField(decimal_places=6, default=0, max_digits=10),
        ),
    ]