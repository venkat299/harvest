# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-14 21:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ledger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opening', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('credit', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('debit', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('closing', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('signal_status', models.CharField(choices=[('PENDING_OPEN', 'PENDING_OPEN'), ('OPEN', 'OPEN'), ('PENDING_CLOSE', 'PENDING_CLOSE'), ('CLOSE', 'CLOSE'), ('NONE', 'NONE')], default='NONE', max_length=20, null=True)),
                ('desc', models.CharField(max_length=64)),
                ('timestamp', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Ndaylow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avg_trade_val', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('avg_hold_inter', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('margin', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('n_day_low', models.IntegerField(default=0)),
                ('order_count', models.IntegerField(default=0)),
                ('profit', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('return_per_day', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('score', models.DecimalField(decimal_places=6, default=0, max_digits=10)),
                ('norm_score', models.DecimalField(decimal_places=6, default=0, max_digits=10)),
                ('allocation', models.DecimalField(decimal_places=6, default=0, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('status', models.CharField(choices=[('PENDING', 'PENDING'), ('COMPLETE', 'COMPLETE'), ('FAILED', 'FAILED')], default='PENDING', max_length=20)),
                ('time', models.DateTimeField()),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('product', models.CharField(max_length=20)),
                ('qty', models.IntegerField(default=0)),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('avg_price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('order_info', models.CharField(max_length=20)),
                ('remote_status', models.CharField(max_length=20, null=True)),
                ('call', models.CharField(max_length=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Signal',
            fields=[
                ('status', models.CharField(choices=[('PENDING_OPEN', 'PENDING_OPEN'), ('OPEN', 'OPEN'), ('PENDING_CLOSE', 'PENDING_CLOSE'), ('CLOSE', 'CLOSE')], default='PENDING_OPEN', max_length=20)),
                ('time', models.DateTimeField()),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('stock', models.CharField(max_length=20)),
                ('series', models.CharField(max_length=2)),
                ('open', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('high', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('low', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('close', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('last', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('prevclose', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('tottrdqty', models.IntegerField(default=0)),
                ('tottrdval', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('timestamp', models.DateField()),
                ('totaltrades', models.IntegerField(default=0)),
                ('isin', models.CharField(max_length=20, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Strategy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('status', models.CharField(choices=[('ACTIVE', 'ACTIVE'), ('INACTIVE', 'INACTIVE')], default='INACTIVE', max_length=10)),
                ('close_type', models.CharField(choices=[('SELL', 'SELL'), ('BUY', 'BUY')], default='SELL', max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Watchlist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('norm_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('exit', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('train_details', models.TextField(default='')),
                ('last_transact_price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('last_qty', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('ACTIVE', 'ACTIVE'), ('INACTIVE', 'INACTIVE'), ('FLUSH', 'FLUSH')], default='INACTIVE', max_length=10)),
                ('signal_status', models.CharField(choices=[('ACTIVE', 'ACTIVE'), ('INACTIVE', 'INACTIVE'), ('FLUSH', 'FLUSH')], default='CLOSE', max_length=20)),
                ('profit_earned', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('hold_active_days', models.IntegerField(default=0)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='harvest.Stock')),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='harvest.Strategy')),
            ],
        ),
        migrations.AddField(
            model_name='strategy',
            name='stocks',
            field=models.ManyToManyField(through='harvest.Watchlist', to='harvest.Stock'),
        ),
        migrations.AddField(
            model_name='signal',
            name='watchlist',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='harvest.Watchlist'),
        ),
        migrations.AddField(
            model_name='order',
            name='signal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='harvest.Signal'),
        ),
        migrations.AddField(
            model_name='ndaylow',
            name='stock',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='harvest.Stock'),
        ),
        migrations.AddField(
            model_name='ndaylow',
            name='strategy',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='harvest.Strategy'),
        ),
        migrations.AddField(
            model_name='ledger',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='harvest.Order'),
        ),
        migrations.AddField(
            model_name='ledger',
            name='signal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='harvest.Signal'),
        ),
        migrations.AddField(
            model_name='ledger',
            name='strategy',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='harvest.Strategy'),
        ),
    ]
