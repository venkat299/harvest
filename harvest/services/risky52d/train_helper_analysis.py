#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import json
import logging
import pandas as pd
import numpy as np
import math
import sqlite3
import os
import concurrent.futures

from django.conf import settings

from harvest.models.ndaylow import Ndaylow
from harvest.models.strategy import Strategy, Stock

#from scipy import stats

import harvest.services.risky52d.predict_helper as predict

log = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL)

conn_db = sqlite3.connect(settings.HIST_DB, check_same_thread = False)
dirpath = settings.BASE_DIR+ settings.DATA_DIRECTORY+'/eod_hist'
# log.debug('name, buy_date ,sell_date,buy, sell, sno, order_id, margin, hold_days, return_per_day, median_turnover, n_day_low, size')

def train(stock_list):

    ## clearing ndaylow table
    strategy = Strategy.objects.get(name='RISKY52D')
    Ndaylow.objects.filter(strategy=strategy).delete()

    ls = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for item in executor.map(train_stock, stock_list, chunksize=20):
            if item is None:
                pass
            else:
                ls.append(item[0])

    if len(ls)<1:
        return False

    result = pd.DataFrame(ls)
    rank_profit = result.profit.rank(pct=True)
    rank_return = result.return_per_day.rank(pct=True)
    rank_count = result.order_count.rank(pct=True)
    result['score'] = rank_profit*rank_return*rank_return*rank_count
    result['norm_score'] = result.profit.rank(pct=True)
    result = result.sort_values(by=['norm_score'], ascending=False)
    result['allocation'] = 0 #settings.R52D_STK_BUDGET * result.norm_score
    # log.debug(ls)
    # log.debug(result)
    for item in result.itertuples():
        # add entry into database
        Ndaylow.objects.create(strategy=strategy,
            stock=Stock.objects.get(stock=item.symbol,series='EQ'),
            avg_hold_inter=item.avg_hold_inter,
            avg_trade_val=item.avg_trade_val,
            margin=item.margin,
            n_day_low=item.n_day_low,
            order_count=item.order_count,
            profit=item.profit,
            return_per_day=item.return_per_day,
            score=item.score,
            norm_score=item.norm_score,
            allocation=float(item.allocation))

    return True

def train_stock(stock):
    symbol = stock.stock
    log.debug(symbol)
    try:
        # read historical eod file
        # file_path = dirpath +'/NSE-' + symbol + '.csv'
        # dt = pd.read_csv(file_path)
        q = "select adj_close as close,TOTTRDVAL as turnover  from eod_yahoo where symbol='{}' and series='EQ' order by timestamp"
        dt = pd.read_sql_query(q.format(symbol), conn_db)
        # dt = dt.rename(columns={'Date':'date','Open':'open','High':'high','Low':'low','Last':'last','Close':'close','Total Trade Quantity':'qty', 'Turnover (Lacs)':'turnover'}) #rename({'Total Trade Quantity':'qty', 'Turnover (Lacs)':'turnover'})
        # dt = dt.sort_values(by=['date'])
        # log.debug(dt.head(5))

        mean_trade_val = round(dt.turnover.mean(),0)
        if mean_trade_val < settings.R52D_TURNOVER:
            # pass
            raise Exception('low trade volume; skipping stock')

        mean_close_val = round(dt.close.mean(),0)
        if mean_close_val < settings.R52D_AVG_PRICE_ATLEAST:
            # pass
            raise Exception('low closing value; skipping stock')

        margin = [1.02,1.04, 1.04,1.08,1.16,1.32,1.64,2.28,3.56] #
        n_day_low = [4, 8, 16, 32, 64, 128, 256, 365]

        result_columns = ['margin','n_day_low','profit', 'order_count']
        result = []
        for y in n_day_low:
        # for x in margin:
            # log.debug('in {} calculating for n_day_low:{}'.format(symbol,y))
            res = calculate_return(dt, margin, y)
            # log.debug('train res--> ',res)
            for item in res:
                if item['result'][0]:
                    (item['result'][1])['symbol'] = symbol
                    (item['result'][1])['avg_trade_val'] = mean_trade_val
                    result.append(item['result'][1])
                
        if len(result) < 2:
            return None


        result_df = pd.DataFrame(result).sort_values(by=['profit'], ascending=False)
        rank_profit = result_df.profit.rank(pct=True)
        rank_return = result_df.return_per_day.rank(pct=True)
        rank_count = result_df.order_count.rank(pct=True)
        result_df['score'] = rank_profit*rank_return*rank_return*rank_count
        result_df = result_df.sort_values(by=['score'], ascending=False)
        final_value = result_df.iloc[0]
        # log.debug(final_value)
        return (final_value,stock)

    except Exception as e:
        log.warn('{} -->  {}'.format(e ,str(symbol)))
        return None

# @numba.jit   
def calculate_return(dt_arr, margin_ls, n_day_low):

    i = 0

    arr = []
    for margin in margin_ls:
        arr.append({
            'margin':margin, 
            'open': False, 
            'amt_avail':1000000, 
            'last_buy_price':0, 
            'op_cl_period':0, 
            'last_buy_qty':0,
            'hold_interval':[],
            'profit':0, 
            'order_count':0,
            'result':(False,{})})

    if len(dt_arr.index) < n_day_low+2:
        return arr

    for close in np.nditer(dt_arr.close[n_day_low:], ['refs_ok'], order='C'):
        n_day_min = dt_arr.close[i:i + n_day_low].min()
        n_day_max = dt_arr.close[i:i + n_day_low].max()

        for item in arr:
            # log.debug(item)
            if predict.stk_open_logic(n_day_max, n_day_min, close) and  item['open'] == False:
                item['open'] = True
                item['last_buy_price'] = close
                item['last_buy_qty'] = math.ceil(item['amt_avail'] / close)
                if item['op_cl_period']==0:
                    item['op_cl_period'] = i

            elif close > (item['last_buy_price'] * item['margin']) and item['last_buy_price'] > 0 and item['open'] == True:
                item['open'] = False
                item['hold_interval'].append(i - item['op_cl_period'])
                item['profit'] = item['profit'] + ((close - item['last_buy_price'])*item['last_buy_qty'])
                item['order_count'] = item['order_count']+1
                
                # reset values
                item['last_buy_price'] = 0
                item['op_cl_period'] = 0
                item['last_buy_qty'] = 0

        i=i+1

    for item in arr:
        if item['order_count'] > 1:
            item['result']=(True, {
                'margin':item['margin'],
                'n_day_low':n_day_low,
                'profit':round(item['profit']/10,0),
                'order_count':item['order_count'],
                'avg_hold_inter':round(float(pd.DataFrame(item['hold_interval']).mean()),0),
                'return_per_day':round(float(item['profit']/(10*pd.DataFrame(item['hold_interval']).sum())),0)
                })

    return arr