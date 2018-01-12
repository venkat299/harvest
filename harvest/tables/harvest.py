# tutorial/tables.py
import django_tables2 as tables
from django_tables2.utils import A
import django_filters 
from django_filters import FilterSet, DateFromToRangeFilter, DateRangeFilter
from django.forms.widgets import SelectDateWidget
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.db import models
import datetime
from calendar import monthrange

from harvest.models.strategy import Strategy, Stock, Watchlist, Order, Signal, Ledger

class LedgerFilter(FilterSet):
    class Meta:
        model = Ledger
        fields = ['strategy__name']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            }
        }
class OrderFilter(FilterSet):
    class Meta:
        model = Order
        fields = ['signal__watchlist__strategy__name']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            }
        }
class SignalFilter(FilterSet):
    class Meta:
        model = Signal
        fields = ['watchlist__strategy__name']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            }
        }

class LedgerTable(tables.Table):
    class Meta:
        model = Ledger
        fields = ['opening', 'credit', 'debit', 'closing', 'strategy', 'desc', 'signal_status', 'timestamp']
        attrs = {"class": "ui striped compact celled table"}
        empty_text = "There are no records matching the search criteria..."

class OrderTable(tables.Table):
    confirm = tables.Column(accessor='uuid', verbose_name='confirm', exclude_from_export=True)
    cancel = tables.Column(accessor='uuid', verbose_name='cancel', exclude_from_export=True)
    class Meta:
        model = Order
        fields = ['signal.watchlist.strategy.name', 'signal.watchlist.stock.stock', 'status', 'qty','price','avg_price','remote_status','call','time', 'uuid']
        attrs = {"class": "ui striped compact celled table"}
        empty_text = "There are no records matching the search criteria..."

    def render_confirm(self,record):
        if record.status != 'PENDING':
            return format_html('''<a ></a>''') 
        # url = reverse('harvest:strategy_confirm_order',kwargs={'uuid': record.uuid, 'avg_price':0})
        return format_html('''
            <a id={} title="Confirm" next:"./", class ='confirm_button' uuid='{}' price={}><i class="checkmark icon"></i></a>
            ''', record.uuid,record.uuid, record.price) 
        
    def render_cancel(self,record):
        if record.status != 'PENDING':
            return format_html('''<a ></a>''') 
        url = reverse('harvest:strategy_cancel_order',kwargs={'uuid': record.uuid})
        return format_html('''
            <a title="Confirm" next:"./", href="{}"><i class="remove circle icon"></i></a>
            ''', url) 

    

class SignalTable(tables.Table):
    class Meta:
        model = Signal
        fields = ['watchlist.strategy.name', 'watchlist.stock.stock', 'status', 'time', 'uuid']
        attrs = {"class": "ui striped compact celled table"}
        empty_text = "There are no records matching the search criteria..."

