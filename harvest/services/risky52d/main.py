import pathlib
import os.path
import datetime
import json
import sqlite3
import pandas as pd
import numpy as np
import math
import json
import collections
from django.db.models import Q
import logging
log = logging.getLogger(__name__)
from django.core.exceptions import ObjectDoesNotExist

from harvest.services.strategy import Strategy as Base
from harvest.models.strategy import Strategy, Stock, Watchlist, Signal, Ledger, Order 
from harvest.models.ndaylow import Ndaylow

import harvest.services.risky52d.train_helper_analysis as train_helper
import harvest.services.risky52d.predict_helper as predict_helper

from django.conf import settings

class Risky52D(Base):

    _id = 1
    _open_type = 'BUY'

    # def __init__(self, strategy):
    # self._conn = sqlite3.connect('./harvest/../../db/harvest.db')

    @staticmethod
    def is_file_latest(filepath):
        """ check if the file is recently downloaded (current quarter)"""
        t = os.path.getmtime(filepath)
        update_month = (datetime.datetime.fromtimestamp(t)).month
        update_yr = (datetime.datetime.fromtimestamp(t)).year
        curr_month = (datetime.date.today()).month
        curr_yr = (datetime.date.today()).year

        #return int((update_month-1)/3) == int((curr_month-1)/3) and curr_yr == update_yr
        return True

    @staticmethod
    def get_stk_list():
        return Stock.objects.filter(series='EQ')

        # conn = sqlite3.connect('db.sqlite3')
        # c = conn.cursor()
        # c.execute('select distinct stock from harvest_stock where series="EQ" order by stock')
        # stock = []
        # for row in c:
        #     stock.append(row[0])
        # return stock

        # """ return list of symbols for which latest eod history is downloaded """
        # mypath = settings.BASE_DIR+ settings.DATA_DIRECTORY+'/eod_hist'
        # # logging.debug(mypath)
        # return [(p.stem)[4:] for p in pathlib.Path(mypath).iterdir() if p.is_file() and 'NSE-' in p.name and Risky52D.is_file_latest(p)]#[1:30]

    @staticmethod
    def allowed_stock_no():
        # conn = sqlite3.connect('harvest/../../db/harvest.db')
        # c = conn.cursor()
        # c.execute('select budget from strategy where strategy="LOW52D"')
        # budget = (c.fetchone())[0]
        # return min(50,int(math.sqrt(budget/10000)*10))
        return settings.R52D_STK_COUNT

    @staticmethod
    def filter_top_symbols(norm_score_arr):
        """ returns index of top 'x' number of with norm score"""
        logging.debug(norm_score_arr)
        no_of_stk = Risky52D.allowed_stock_no()
        result = []

        if no_of_stk == 0 or len(norm_score_arr) == 0:
            return result
        else:
            res = norm_score_arr.nlargest(no_of_stk,0)
            logging.debug(res)
            for x,y in res.iterrows():
                result.append(x)
            return result
    
    @staticmethod
    def open_stk():        
        open_stk = Signal.objects.filter(watchlist__strategy__name='RISKY52D').exclude(status ='Open').values_list('watchlist__stock__stock', flat=True)
        return open_stk

    @staticmethod
    def curr_stk():  # get list of all stock on watchlist      
        curr_stk = Watchlist.objects.filter(strategy__name='RISKY52D').values_list('stock__stock', flat=True)
        return curr_stk

    @staticmethod
    def train():
        # logging.debug(item.stock.stock)
        # get list of all stock
        # train each stock using its historical value
        # aggregate result
        # filter top performing stocks
        # again tune parameters for filtered stock
        # save to database
        ####
        # strategy
        t = ('RISKY52D',)
        stk_ls = Risky52D.get_stk_list()
        logging.debug(stk_ls)

        if(train_helper.train(stk_ls)):
            Risky52D.load_into_watchlist()
        # Risky52D.load_into_watchlist()

        log.info('training completed')
        return {"success": True}

    @staticmethod
    def predict():
        return predict_helper.execute()

    @staticmethod
    def reset():
        strategy = Strategy.objects.get(name='RISKY52D')
        Ledger.objects.filter(~Q(desc='RISKY52D/CASHIN'),desc__icontains='RISKY52D').delete()
        Order.objects.filter(signal__watchlist__strategy=strategy).delete()
        Signal.objects.filter(watchlist__strategy=strategy).delete()
        Watchlist.objects.filter(strategy=strategy).delete()
        return {"success": True}
        #return predict_helper.execute()

    @staticmethod
    def load_into_watchlist():
        curr_stk = Risky52D.curr_stk()
        open_stk = Risky52D.open_stk()

        stk_count = settings.R52D_STK_COUNT
        budget_max = settings.R52D_STK_BUDGET_MAX
        budget_min = settings.R52D_STK_BUDGET_MIN

        final_entries = Ndaylow.objects.filter(avg_hold_inter__gte=5).order_by('-norm_score')[:stk_count]
        # setting allocation 
        i=0
        for item in final_entries:
            item.allocation =budget_min+((stk_count-i)*(budget_max-budget_min)/stk_count)
            item.save()
            i=i+1

        # set 'INACTIVE' status to existing stocks which doesn't satisfy the criteria
        for item in curr_stk:
            stk = Watchlist.objects.get(strategy__name='RISKY52D', stock__stock=item)
            stk.status = 'INACTIVE'
            stk.save()
        # set 'FLUSH' status to open stocks which doesn't satisfy the criteria 
        for item in open_stk:
            stk = Watchlist.objects.get(strategy__name='RISKY52D', stock__stock=item)
            stk.status = 'INACTIVE'# 'FLUSH'
            stk.save()
        # # add new stocks to table and set status to active
        for item in final_entries:
            if item.stock.stock in open_stk:
                stk = Watchlist.objects.get(strategy__name='RISKY52D', stock__stock=item.stock.stock)
                stk.status = 'ACTIVE'
                stk.norm_score=item.norm_score
                stk.scores = item.score
                stk.exit = item.margin
                stk.train_details = str(item) 
                stk.save()
            elif item.stock.stock in curr_stk:
                stk = Watchlist.objects.get(strategy__name='RISKY52D', stock__stock=item.stock.stock)
                stk.status = 'ACTIVE'
                stk.norm_score=item.norm_score
                stk.scores = item.score
                stk.exit = item.margin
                stk.train_details = str(item)
                stk.save()
            else:
                log.debug(item)
                try:
                    stk = item.stock
                    strategy = Strategy.objects.get(name='RISKY52D')
                    # print(item)
                    Watchlist.objects.create(strategy=strategy, stock=stk,
                        norm_score=item.norm_score,
                        score = item.score,
                        exit = item.margin,
                        #n_day = item.n_day_low,
                        train_details = str(item),
                        status = 'ACTIVE')
                except ObjectDoesNotExist as e:
                    log.warn('{} -->  {}'.format(e ,str(item)))

    def schedule_task(self):
        pass

    # def save(self):
    #     cursor = self._conn.cursor()
    #     cursor.execute('''delete from strategy
    #                       where strategy=?''',
    #                    (self.strategy,))
    #     cursor.execute('''INSERT INTO strategy
    #                       VALUES (?,?,?,?)''',
    #                    self._get_display_values())
    #     self._conn.commit()
