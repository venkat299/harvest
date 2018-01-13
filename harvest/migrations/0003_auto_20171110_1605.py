# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-11-10 10:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('harvest', '0002_auto_20171110_1357'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='stock',
        ),
        migrations.RemoveField(
            model_name='order',
            name='strategy',
        ),
        migrations.RemoveField(
            model_name='signal',
            name='stock',
        ),
        migrations.RemoveField(
            model_name='signal',
            name='strategy',
        ),
        migrations.AddField(
            model_name='signal',
            name='watchlist',
            field=models.ForeignKey( on_delete=django.db.models.deletion.CASCADE, to='harvest.Watchlist'),
            preserve_default=False,
        ),
    ]