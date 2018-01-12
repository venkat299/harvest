import logging
from datetime import datetime
from django.utils import timezone
import logging
import uuid
import decimal

from django.conf import settings
from harvest.models.strategy import Strategy, Stock, Watchlist, Signal, Order, Ledger
from harvest.services import order, ledger

def open(watchlist, quantity, price,**other):
    # case: 'Close' --> 'Pending_Open'
    close_type = watchlist.strategy.close_type
    call_type = 'BUY'
    if close_type=='BUY':
        call_type = 'SELL'

    signal_id = str(uuid.uuid4())
    my_signal = Signal.objects.create(watchlist=watchlist, time=timezone.now(), uuid=signal_id, status='PENDING_OPEN')
    watchlist.signal_status = 'PENDING_OPEN'
    watchlist.save()

    my_order = order.place(my_signal,call_type, quantity, price, **other)
    if call_type == 'BUY':
        ledger.order_entry(my_order, my_signal, 'debit')
    else:
        ledger.order_entry(my_order, my_signal, 'credit')

    return (True, my_signal, my_order)

def close(watchlist, price, **other):
    # case: 'Open' --> 'Pending_Close'
    call_type = watchlist.strategy.close_type
    my_signal = Signal.objects.get(watchlist=watchlist, status='OPEN')
    my_signal.status = 'PENDING_CLOSE'
    my_signal.save()
    watchlist.signal_status = 'PENDING_CLOSE'
    watchlist.save()

    prev_order = Order.objects.get(signal=my_signal, status='COMPLETE')
    my_order = order.place(my_signal,call_type, prev_order.qty, price, **other)
    return (True, my_signal, my_order)

def confirm(my_order, my_signal):
    close_type = my_signal.watchlist.strategy.close_type
    call_type = my_order.call

    if close_type==call_type and my_signal.status=='PENDING_CLOSE':
        # case: 'Pending_Close' --> 'Close'
        my_signal.status = 'CLOSE'
        my_signal.save()
        my_signal.watchlist.signal_status = 'CLOSE'
        my_signal.watchlist.save()
        
        open_type = 'BUY'
        if close_type=='BUY':
            open_type=='SELL'
        # calculating profit/loss
        open_order = Order.objects.get(signal=my_signal,call=open_type, status='COMPLETE')
        close_order = my_order
        open_amt = open_order.qty*open_order.avg_price
        close_amt = close_order.qty*close_order.avg_price

        if close_type == 'SELL':
            open_amt = open_amt*(-1)
            ledger.order_entry(my_order, my_signal, 'credit')
        else:
            close_amt = close_amt*(-1)
            ledger.order_entry(my_order, my_signal, 'debit')

        profit = decimal.Decimal(open_amt)+decimal.Decimal(close_amt)
        # print('open_amt: {}, close_amt : {}'.format(open_amt, close_amt))
        # print('close_type: {}, profit : {}'.format(close_type, profit))
        my_signal.watchlist.profit_earned = profit + my_signal.watchlist.profit_earned 
        my_signal.watchlist.save()
        # todo calculate hold days

    elif my_signal.status=='PENDING_OPEN':
        # case: 'Pending_Open' --> 'Open'
        my_signal.status = 'OPEN'
        my_signal.save()
        my_signal.watchlist.signal_status = 'OPEN'
        my_signal.watchlist.last_transact_price = my_order.avg_price
        my_signal.watchlist.last_qty = my_order.qty
        my_signal.watchlist.save()
        if my_order.price != my_order.avg_price:
            if my_order.price < my_order.avg_price:
                if call_type=='BUY':
                    ledger.add_reconcile(my_order, my_signal, 'debit', decimal.Decimal(my_order.avg_price)-decimal.Decimal(my_order.price))
                else:
                    ledger.add_reconcile(my_order, my_signal, 'credit', decimal.Decimal(my_order.avg_price)-decimal.Decimal(my_order.price))
            else:
                if call_type=='BUY':
                    ledger.add_reconcile(my_order, my_signal, 'credit', decimal.Decimal(my_order.price)-decimal.Decimal(my_order.avg_price))
                else:
                    ledger.add_reconcile(my_order, my_signal, 'debit', decimal.Decimal(my_order.price)-decimal.Decimal(my_order.avg_price))
    

    return my_signal

def cancel(my_order, my_signal):
    close_type = my_signal.watchlist.strategy.close_type
    call_type = my_order.call

    if close_type==call_type:
        # case: 'Pending_Close' --> 'Open'
        if my_signal.status=='PENDING_CLOSE':
            my_signal.status = 'OPEN'
            my_signal.save()
            my_signal.watchlist.signal_status = 'OPEN'
            my_signal.watchlist.save()
    else:
        # case: 'Pending_Open' --> 'Close'
        if my_signal.status=='PENDING_OPEN':
            my_signal.status = 'CLOSE'
            my_signal.save()
            my_signal.watchlist.signal_status = 'CLOSE'
            my_signal.watchlist.save()
            if call_type=='BUY':
                ledger.order_entry(my_order, my_signal, 'credit')
            else:
                ledger.order_entry(my_order, my_signal, 'debit')

    return my_signal

