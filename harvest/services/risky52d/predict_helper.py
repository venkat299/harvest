# from harvest.mail import mailer
import json
import uuid
import sys
import sqlite3
import json
import logging
import pandas as pd
import logging
from datetime import datetime
from pytz import timezone
from ast import literal_eval as make_tuple

import logging
 
# import quandl

# logging.basicConfig(level=logging.DEBUG, filename="logfile.log",filemode="a+",format="%(message)s")
from datetime import datetime
from django.db.models import Prefetch
from django.conf import settings
from harvest.models.strategy import Strategy, Stock, Watchlist, Signal, Order, Ledger
from harvest.models.ndaylow import Ndaylow
from harvest.services import signal, ledger


log = logging.getLogger(__name__)

dbpath = settings.BASE_DIR+'/'+settings.HIST_DB


def get_cl_nday_max_min(symbol, n_day):
    conn_db = sqlite3.connect(dbpath)
    cursor = conn_db.cursor()
    cursor.execute(
        'select timestamp as date, adj_close as close from eod_yahoo where symbol=? order by timestamp desc limit ?', (symbol,n_day))
    db_rows = cursor.fetchall()
    # log.debug('db_rows:',db_rows)
    rows = pd.DataFrame(db_rows, columns=['date', 'close'])
    if len(rows) < n_day:
        log.debug('skipping predict: less than {} entries in eod table'.format(n_day,))
        return (None, None)
    else:
        log.debug('max close value for symbol {} is {}'.format(
            symbol, (rows['close']).min()))
        return ((rows['close']).min(),(rows['close']).max())


def stk_open_logic(max_of, min_of, curr):
    # band = max_of - min_of
    # logging.debug('comparing price  curr:{} cl_52_min:{} cl_52_max:{} calc:{} signal:{} '.format(
    #          curr, min_of, max_of, 
    #          ((max_of - min_of) * settings.R52D_MARGIN)+ min_of,
    #          curr <= ((max_of - min_of) * settings.R52D_MARGIN)+ min_of))
    return curr <= (((max_of - min_of) * settings.R52D_MARGIN)+ min_of)
         


def predict(opt):
    exit = opt.exit
    status = opt.signal_status
    ltp = opt.stock.close
    buy_price = opt.last_transact_price
    # print((opt.train_details))
    # print(make_tuple(opt.train_details[12:-1])[4])
    # print(int(float(make_tuple(opt.train_details[12:-1])[4][1])))
    n_day = Ndaylow.objects.get(strategy=opt.strategy,stock=opt.stock).n_day_low
    signal = None
    # possible status [NONE, PENDING_OPEN, OPEN, PENDING_CLOSE, CLOSE]
    # if status not in ['PENDING_OPEN','OPEN','PENDING_CLOSE']:
    log.debug('applying prediction for stock: {} '.format(opt))

    symbol =  opt.stock.stock
    (cl_52_min, cl_52_max) = get_cl_nday_max_min(symbol, n_day)


    if ltp:
        if status == 'CLOSE':
            # opt contains row
            # (strategy,symbol, norm_score,exit,status,eod,buy_price)
            if cl_52_max is None:
                return None

            if stk_open_logic(cl_52_max, cl_52_min, ltp):  # TODO optimize this margin
                signal = 'BUY'

        if status == 'OPEN':
            if ltp >= (buy_price * exit):
                signal = 'SELL'
    else:
        log.warn('problem ltp is none')

    # if cl_52_max:
    logging.info('comparing close price stock: {} close:{} cl_52_max:{} cl_52_min:{} calc:{} signal:{} value:{} '.format(
            symbol, ltp, cl_52_max, cl_52_min , (((cl_52_max - cl_52_min) * settings.R52D_MARGIN)+ cl_52_min),signal,stk_open_logic(cl_52_max, cl_52_min, ltp)))
    # logging.debug('prediction result for stock: {} result:{}'.format(opt, signal))

    return signal

def get_current_avail(strategy_name):
    return Ledger.objects.filter(strategy__name=strategy_name).latest('timestamp').closing

def execute():
    # ls  = Watchlist.objects.filter(strategy__name='RISKY52D')
    # logging.debug(ls)

    logging.debug('in predict.execute()')
    qs = Watchlist.objects.filter(strategy__name='RISKY52D', status='ACTIVE')

    mail_entries=[]
    avail_amt = get_current_avail('RISKY52D')
    logging.info(' available_amt : {}'.format(avail_amt))
    for item in qs:
        val = predict(item)
        exit = item.exit
        status = item.signal_status
        ltp = item.stock.close
        buy_price = item.last_transact_price
        logging.debug(val)
        
        if val == 'BUY':
            allocated_amt = Ndaylow.objects.get(stock=item.stock, strategy=item.strategy).allocation
            profit_earned = item.profit_earned
            per_stk_budget = allocated_amt + profit_earned
            open_ord_qty = round(per_stk_budget / ltp)
            buy_amt = round(ltp * open_ord_qty)
            log.info('avail_amt:{}, required_amt:{}, stk:{}, ltp:{}, qty :{}'.format(avail_amt, buy_amt, item.stock.stock, ltp, open_ord_qty))

            if avail_amt > buy_amt and open_ord_qty > 0: # buy
                (x,y,my_order) = signal.open(item, open_ord_qty, ltp)
                
                avail_amt = get_current_avail('RISKY52D')
                # update mail content
                mail_entries.append(str(my_order))
            else:
                mail_entries.append(str(
                    (item.strategy.name, item.stock.stock, 'ERR: Couldnt signal PENDING_OPEN insufficient funds')))
        
        elif val == 'SELL':
            (x,y,my_order) = signal.close(item, ltp)
            avail_amt = get_current_avail('RISKY52D')
            # update mail content
            mail_entries.append(str(my_order))



    log.info(mail_entries)

    # conn.commit()
    # if len(mail_entries) > 0:
    #     try:
    #         pass
    #         # mailer.mail(('LOW52D Prediction', '\n'.join(mail_entries)))
    #     except Exception as e:
    #         log.error(e)
    return {"success": True}
