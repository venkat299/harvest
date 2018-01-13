import logging
from datetime import datetime
from django.utils import timezone
import logging
import uuid
import decimal

from django.conf import settings
from harvest.models.strategy import Strategy, Stock, Watchlist, Signal, Order, Ledger


def get_current_avail(strategy_name):
    curr_avail = None
    try:
        entry = Ledger.objects.filter(strategy__name=strategy_name).latest('timestamp')
        return entry.closing
    except Ledger.DoesNotExist as e:
        print(e)
        return None


def add_fund(strategy, amt):
    if amt <=0:
        return {"success": False, "msg":"Amount is not positive"}
    opening = get_current_avail(strategy.name)
    if opening is None:
        opening = 0

    fund_entry(opening, amt, 0, (opening)+amt, strategy, 'CASHIN')
    return {"success": True, "avail_fund":get_current_avail(strategy.name) }

def pull_fund(strategy, amt):
    if amt <=0:
        return {"success": False, "msg":"Amount is not positive"}
    opening = get_current_avail(strategy.name)
    if opening < amt:
        return {"success": False, "msg":"Insufficient fund"}

    fund_entry(opening, 0, amt, (opening)-amt, strategy, 'CASHOUT')
    return {"success": True, "avail_fund":get_current_avail(strategy.name) }


def fund_entry(opening, credit, debit, closing, strategy, desc):
    Ledger.objects.create(
        opening = opening, 
        credit = credit,
        debit = debit,
        closing = closing,
        strategy = strategy,
        signal = None,
        signal_status = None, 
        order = None,
        desc = strategy.name+'/'+desc,
        timestamp = timezone.now()
        )


def order_entry(order, signal, type):
    # buy-sell case:
    #
    # add debit entry in ledger when 'Close' --> 'Pending_Open'
    # rollback debit entry when 'Pending_Open' --> 'Close'
    # no entry when status changes from 'Pending_Open' --> 'Open'
    #
    # no entry when status changes from 'Open' --> 'Pending_Close'
    # no entry when status changes from 'Pending_Close' --> 'Open'
    # add credit entry in ledger when 'Pending_Close' --> 'Close'
    #
    # sell-buy case:
    # TODO

    strategy = signal.watchlist.strategy
    curr = get_current_avail(strategy.name)

    opening = curr
    credit = 0
    debit = 0
    closing = curr
    if type =='debit':
        debit = order.qty * order.price
        closing = closing - debit
    else:
        credit = order.qty * order.price
        closing = closing + credit

    Ledger.objects.create(
        opening = opening, 
        credit = credit,
        debit = debit,
        closing = closing,
        strategy = strategy,
        signal = signal,
        signal_status = signal.status, 
        order = order,
        desc = strategy.name+'/'+signal.watchlist.stock.stock,
        timestamp = timezone.now()
        )

def add_reconcile(order, signal, type, value):
    strategy = signal.watchlist.strategy
    curr = get_current_avail(strategy.name)

    opening = curr
    credit = 0
    debit = 0
    closing = curr
    if type =='debit':
        debit = order.qty * value
        closing = closing - value
    else:
        credit = order.qty * value
        closing = closing + value

    Ledger.objects.create(
        opening = opening, 
        credit = credit,
        debit = debit,
        closing = closing,
        strategy = strategy,
        signal = signal,
        signal_status = signal.status, 
        order = order,
        desc = strategy.name+'/'+signal.watchlist.stock.stock,
        timestamp = timezone.now()
        )


