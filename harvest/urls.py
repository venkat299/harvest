from django.conf.urls import url

from .views import harvest, strategy
app_name = 'harvest'
urlpatterns = [
    # ex: /strategy/
    url(r'^$', harvest.HarvestView.as_view(), name='home'),

    url(r'^strategy/$', harvest.StrategyView.as_view(), name='strategy'),
    url(r'^stocks/$', harvest.StockView.as_view(), name='stock'),
    url(r'^(?P<strategy_id>[0-9]+)/$', harvest.watchlist, name='watchlist'),

    url(r'^strategy/train/(?P<strategy_id>[0-9]+)/$', strategy.train, name='strategy_train'),
    url(r'^strategy/predict/(?P<strategy_id>[0-9]+)/$', strategy.predict, name='strategy_predict'),
    url(r'^strategy/confirm_order/(?P<uuid>[0-9a-f-]+)/(?P<avg_price>\d+\.\d{2})/$', strategy.confirm_order, name='strategy_confirm_order'),
    url(r'^strategy/cancel_order/(?P<uuid>[0-9a-f-]+)/$', strategy.cancel_order, name='strategy_cancel_order'),
    url(r'^strategy/reset/(?P<strategy_id>[0-9]+)/$', strategy.reset, name='strategy_reset'),

    # url(r'^ledger/list/$', harvest.LedgerListView.as_view(
    #     # model=Ledger,
    #     # table_class=LedgerTable, 
    #     # template_name='ledger/index.html' , 
    #     # filter_class = LedgerFilter, 
    # ) , name='ledger_list'),
    # url(r'^order/(?P<strategy_id>[0-9]+)/$', harvest.order_jtable.as_view() , name='order_jtable'),
    # url(r'^order/get/(?P<strategy_id>[0-9]+)/$', harvest.order_jtable_list.as_view() , name='order_jtable_list'),
    

    url(r'^order/list/$', harvest.OrderListView.as_view() , name='order_list'),

    url(r'^signal/list/$', harvest.SignalListView.as_view() , name='signal_list'),
    url(r'^signal/close/(?P<watchlist_id>[0-9]+)/$', harvest.close_signal, name='close_signal'),

    url(r'^ledger/list/$', harvest.LedgerListView.as_view() , name='ledger_list'),
    url(r'^ledger/add_fund/(?P<strategy_id>[0-9a-f-]+)/(?P<amt>\d+\.\d{2})/$', harvest.add_fund, name='add_fund'),
    url(r'^ledger/pull_fund/(?P<strategy_id>[0-9a-f-]+)/(?P<amt>\d+\.\d{2})/$', harvest.pull_fund, name='pull_fund'),


]


import harvest.scheduler.scheduler