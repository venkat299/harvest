from django.shortcuts import render, get_object_or_404
from django.views import generic
from django_filters.views import FilterView
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, TemplateView
from braces.views import LoginRequiredMixin
from braces.views import GroupRequiredMixin

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query_utils import Q
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_list_or_404, get_object_or_404, render, render_to_response
from django_tables2 import SingleTableView, RequestConfig
from django_tables2.export.views import ExportMixin

from dal import autocomplete
from django.db.models import Count, Case,Sum, When, IntegerField, CharField
from django.db.models.functions import Substr
from django.db.models.expressions import Value
from django.contrib.auth.decorators import user_passes_test


import datetime
import decimal
from itertools import chain


# from django.http import HttpResponse

from harvest.models.strategy import Strategy, Stock, Watchlist, Order, Signal, Ledger
from harvest.tables.harvest import LedgerTable, LedgerFilter, OrderTable, OrderFilter, SignalTable, SignalFilter
from harvest.forms.harvest import LedgerFormHelper, OrderFormHelper, SignalFormHelper
from harvest.services import signal, ledger

class HarvestView(generic.ListView):
    template_name = 'home/index.html'
    context_object_name = 'user_strategy_list'

    def get_queryset(self):
        """Return the last five items."""
        return Strategy.objects.order_by('-name')  # [:5]


class StrategyView(generic.ListView):
    template_name = 'strategy/index.html'
    context_object_name = 'user_strategy_list'

    def get_queryset(self):
        return Strategy.objects.annotate(prof=Sum('watchlist__profit_earned'))


class StockView(generic.ListView):
    template_name = 'stock/index.html'
    context_object_name = 'user_stock_list'

    def get_queryset(self):
        return Stock.objects.order_by('stock')


# class SignalView(generic.ListView):
#     template_name = 'signal/index.html'
#     context_object_name = 'user_stock_list'

#     def get_queryset(self):
#         return Signal.objects.order_by('-time')


# class OrderView(generic.ListView):
#     template_name = 'order/index.html'
#     context_object_name = 'user_stock_list'

#     def get_queryset(self):
#         return Order.objects.order_by('-time')


class PagedFilteredTableView(ExportMixin, SingleTableView):
    filter_class = None
    formhelper_class = None
    context_filter_name = 'filter'
    # exclude_column = ('x_edit','x_transfer','x_promote','x_terminate')

    def get_queryset(self, **kwargs):
      qs = super(PagedFilteredTableView, self).get_queryset()
      self.filter = self.filter_class(self.request.GET, queryset=qs)
      self.filter.form.helper = self.formhelper_class()
      return self.filter.qs

    def get_context_data(self, **kwargs):
      context = super(PagedFilteredTableView, self).get_context_data()
      context[self.context_filter_name] = self.filter
      return context

class LedgerListView(PagedFilteredTableView):
    model = Ledger
    template_name = 'ledger/index.html'
    context_object_name = 'ledger_list'
    # ordering = ['e_name']
    # group_required = u'area_apms'
    table_class = LedgerTable
    filter_class = LedgerFilter
    formhelper_class = LedgerFormHelper

    def get_queryset(self):
        qs = super(LedgerListView, self).get_queryset()
        return qs
    
    def post(self, request, *args, **kwargs):
        return PagedFilteredTableView.as_view()(request)

    def get_context_data(self, **kwargs):
        context = super(LedgerListView, self).get_context_data(**kwargs)
        context['nav_customer'] = True
        search_query = self.get_queryset()
        # print(search_query.query)
        table = LedgerTable(search_query)
        RequestConfig(self.request, paginate={'per_page': 40}).configure(table)
        context['table'] = table
        context['total_rows'] = search_query.count()
        # print(context['total_rows'])
        return context

class OrderListView(PagedFilteredTableView):
    model = Order
    template_name = 'order/index.html'
    context_object_name = 'ledger_list'
    # ordering = ['e_name']
    # group_required = u'area_apms'
    table_class = OrderTable
    filter_class = OrderFilter
    formhelper_class = OrderFormHelper

    def get_queryset(self):
        qs = super(OrderListView, self).get_queryset()
        return qs
    
    def post(self, request, *args, **kwargs):
        return PagedFilteredTableView.as_view()(request)

    def get_context_data(self, **kwargs):
        context = super(OrderListView, self).get_context_data(**kwargs)
        context['nav_customer'] = True
        search_query = self.get_queryset()
        # print(search_query.query)
        table = OrderTable(search_query)
        RequestConfig(self.request, paginate={'per_page': 40}).configure(table)
        context['table'] = table
        context['total_rows'] = search_query.count()
        # print(context['total_rows'])
        return context

class SignalListView(PagedFilteredTableView):
    model = Signal
    template_name = 'signal/index.html'
    context_object_name = 'ledger_list'
    # ordering = ['e_name']
    # group_required = u'area_apms'
    table_class = SignalTable
    filter_class = SignalFilter
    formhelper_class = SignalFormHelper

    def get_queryset(self):
        qs = super(SignalListView, self).get_queryset()
        return qs
    
    def post(self, request, *args, **kwargs):
        return PagedFilteredTableView.as_view()(request)

    def get_context_data(self, **kwargs):
        context = super(SignalListView, self).get_context_data(**kwargs)
        context['nav_customer'] = True
        search_query = self.get_queryset()
        # print(search_query.query)
        table = SignalTable(search_query)
        RequestConfig(self.request, paginate={'per_page': 40}).configure(table)
        context['table'] = table
        context['total_rows'] = search_query.count()
        # print(context['total_rows'])
        return context

def watchlist(request, strategy_id):
    total_gain = 0
    total_unreal = 0
    total_fund_avail = 0
    strategy = Strategy.objects.get(id=strategy_id)
    try:
        watchlist_ls = Watchlist.objects.filter(strategy=strategy_id).order_by('-signal_status','profit_earned')
        for item in watchlist_ls:
            total_gain = total_gain + item.profit_earned
            if item.signal_status=='OPEN':
                item.unreal_gain = (item.stock.close - item.last_transact_price) * item.last_qty
                total_unreal = total_unreal + item.unreal_gain
            else:
                item.unreal_gain=''
        total_fund_avail = ledger.get_current_avail(strategy.name)

    except Watchlist.DoesNotExist:
        raise Http404("watchlist does not exist")
    return render(request, 'watchlist/'+strategy.name+'_index.html', {'user_watchlist': watchlist_ls,
            'total_gain':total_gain,
            'total_unreal':total_unreal,
            'total_fund_avail':total_fund_avail,
            'strategy':strategy
            })

def close_signal(request, watchlist_id):
    response = {"success":False}
    try:
        watchlist = Watchlist.objects.get(id=watchlist_id)
        signal.close(watchlist, watchlist.stock.close)
        response = {"success": True}
    except Exception as e:
        raise e
    return JsonResponse(response, safe=False)

def add_fund(request, strategy_id, amt):
    amt = decimal.Decimal(amt)
    response = {"success":False}
    try:
        strategy = Strategy.objects.get(id=strategy_id)
        response = ledger.add_fund(strategy, amt)
    except Exception as e:
        raise e
    return JsonResponse(response, safe=False)

def pull_fund(request, strategy_id, amt):
    amt = decimal.Decimal(amt)
    response = {"success":False}
    try:
        strategy = Strategy.objects.get(id=strategy_id)
        response = ledger.pull_fund(strategy, amt)
    except Exception as e:
        raise e
    return JsonResponse(response, safe=False)


# class WatchlistView(generic.ListView):
#     template_name = 'watchlist/index.html'
#     context_object_name = 'user_watchlist'

#     def get_queryset(self):
#         # """Return the last five items."""
#         print(str(self.que))
#         Watchlist.objects.filter(strategy=self.request.strategy_id).order_by('norm_score')
#         # # [:5]


# def index(request):
#     user_strategy_list = Strategy.objects.order_by('-name')[:5]
#     context = {
#         'user_strategy_list': user_strategy_list,
#     }
#     return render(request, 'strategy/index.html', context)

    # stock_list = get_object_or_404(Watchlist, strategy=strategy_id)
    # return render(request, 'watchlist/index.html', {'user_watchlist':
    # stock_list})


