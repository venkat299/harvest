#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import json
import logging
import pandas as pd
import numpy as np
import math
import os

from django.conf import settings

#from scipy import stats

import harvest.services.risky52d.predict_helper as predict

log = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL)

dirpath = settings.BASE_DIR+ settings.DATA_DIRECTORY+'/eod_hist'

def train(opt):
    # simple JSON echo script
    # lines = sys.stdin.readlines()
    # #log.debug('input lines:%s data:%s',len(lines),lines)
    # opt = json.loads(lines[len(lines)-1])
    #log.debug(opt)
    # #log.debug(opt['python_dir'])    
    file_path = dirpath +'/NSE-' + opt + '.csv'
    # if not os.path.exists("/does/not/exist"):
    #     raise Exception('CSV file not found for '+ dirpath)
    dt = pd.read_csv(file_path)
    dt_length = len(dt)
    #log.debug(dt.columns)
    #log.debug('len(dt):%s', len(dt))
    #log.debug(dt.head(5))
    #log.debug(dt.tail(5))
    #print('Processing Stock:%s',opt)
     # converting to array
    dt_arr = dt.as_matrix()[::-1, :]
    # check if trade value is above certain avg limit (100 crore =1000) 100 00 00 000
    mean_trade_val = dt_arr[:, 7].mean()
    if mean_trade_val < settings.R52D_TURNOVER:
        raise Exception('low trade volume skip stock')

    margin = [1.025,1.05,1.075,1.1,1.125,1.15,1.20,1.20,1.25,1.30,1.35]
    
    res_ls=[]
    ror_ls=[]
    for x in margin:
        run_result=find_max(dt_arr,x)
        if run_result[0]:
            #log.debug('%s:::margin:%s==>%s',opt,x,run_result[1])
            res_ls.append(run_result[1])
            ror_ls.append(run_result[1]['ror'])
        #else:
            #log.debug('%s:::margin:%s==>no transaction',opt,x,)
            
    if len(ror_ls)>0:
        result = {}
        result = res_ls[ror_ls.index(max(ror_ls))]
        result['strategy_id'] = 'LOW52D'
        result['tradingsymbol'] = opt
        return result
    else:
        return None


def find_max(dt_arr,margin):
    close_t0 = dt_arr[:, 5]
    fixed_limit = 10000
    variable_limit = 10000
    fixed_limit_profit = 0
    variable_limit_profit = 0
    fixed_returns = []
    n = 0
    open = False
    last_buy_price = 0
    profit = 0
    order_cycles = 0
    op_cl_period = 0
    op_cl_periods = []
    fixed_qty = 0
    variable_qty = 0
    for curr in np.nditer(close_t0[52:], ['refs_ok'], order='C'):
        temp_min = close_t0[n:n + 52].min()
        temp_max = close_t0[n:n + 52].max()
        # TODO optimize this margin
        if predict.stk_open_logic(temp_max, temp_min, curr):
            open = True
            last_buy_price = curr
            fixed_qty = math.ceil(fixed_limit / curr)
            variable_qty = math.ceil(variable_limit / curr)
            if op_cl_period==0:
                op_cl_period = n
        elif curr > (last_buy_price * margin) and last_buy_price > 0:
            open = False
            fixed_limit_profit = fixed_limit_profit + (last_buy_price
                    - curr) * -1 * fixed_qty
            variable_limit_profit = variable_limit_profit \
                + (last_buy_price - curr) * -1 * variable_qty
            variable_limit = variable_limit + variable_limit_profit
            fixed_returns.append(round((last_buy_price - curr) * -1
                                 * fixed_qty, 2))
            order_cycles = order_cycles + 1
            op_cl_periods.append(n - op_cl_period)
             # reset values
            last_buy_price = 0
            op_cl_period = 0
            fixed_qty = 0
            variable_qty = 0
        ##log.debug('==> n:%s curr:%s max:%s min:%s margin:%s open:%s fixed_profit:%s varied_profit:%s op_cl_period:%s',n,curr,temp_max,temp_min,temp_min_margin,open,fixed_limit_profit,variable_limit_profit,op_cl_period),
        n = n + 1
        
    #log.debug(n)
    #log.debug('order_cycles:%s', order_cycles)
    #log.debug(op_cl_periods)
    if order_cycles<=1:
        return (False,{})
    df_std = pd.DataFrame(fixed_returns)
    df_hold_days = pd.DataFrame(op_cl_periods)
    returns_std = df_std.std()  # /df_std.mean()
    returns_mean = df_std.mean()
    returns_median = df_std.median()
    hold_days_mean= df_hold_days.median()
    hold_days_std = df_hold_days.std()
    score = (returns_median*order_cycles*order_cycles/returns_std)

    res = {}
    res['strategy_score'] =  round(float(score),2)
    res['returns_mean'] =  round(float(returns_mean))
    res['margin'] =  round(float(margin),4)
    res['returns_std'] =round(float(returns_std), 4)
    res['score'] = round(float(score),4)
    res['hold_days_mean'] = round(float(hold_days_mean))
    res['returns_median'] = round(float(returns_median))
    res['order_cycles'] = order_cycles
    res['ror'] = round(float(variable_limit_profit / fixed_limit), 4)
    res['extra_debug'] = {'cycle_periods': op_cl_periods,
                          'fixed_returns': fixed_returns,
                          'order_cycles': order_cycles,
                          'score':round(float(score),4),
                          'returns_median':round(float(returns_median)),
                          'returns_std':round(float(returns_std),4),
                          'hold_days_mean':round(float(hold_days_mean)),
                          'hold_days_std':round(float(hold_days_std),4)}
    return (True,res)


