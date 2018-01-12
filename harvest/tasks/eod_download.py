""" downloads eod history for the stocks available from NSE website """
import os.path
import datetime
import sys
import json
import csv
import quandl
import pandas as pd
import sqlite3
import urllib.request
import urllib.parse
from yahoo_historical import Fetcher
from django.conf import settings

import logging
# logging.basicConfig(level=logging.DEBUG,
# filename="log/python.log",filemode="w",format="%(message)s")
log = logging.getLogger(__name__)
from harvest.models.strategy import Strategy, Stock

api_key = settings.QUANDL_API_KEY
quandl.ApiConfig.api_key = api_key

# https://www.quandl.com/api/v3/datasets/NSE/YESBANK.csv?api_key=1CzVT1zp5yzCQjQNq8yR&limit=1095


def is_file_latest(filepath):
    """ check if the file is recently downloaded (current quarter)"""
    try:
        t = os.path.getmtime(filepath)
        update_month = (datetime.datetime.fromtimestamp(t)).month
        update_yr = (datetime.datetime.fromtimestamp(t)).year
        curr_month = (datetime.date.today()).month
        curr_yr = (datetime.date.today()).year
        return int((update_month-1)/3) == int((curr_month-1)/3) and curr_yr == update_yr

    except FileNotFoundError as e:
        log.warn('file not found for: {}, exception:{}'.format(filepath, e))
        return False

        

def upload_to_hist_db(stock_ls):
    conn_db2 = sqlite3.connect(settings.HIST_DB)
    curs_db2 = conn_db2.cursor()
    for item in stock_ls:
        try:
            file_path = dest = 'harvest/data/eod_hist/NSE-'+item+'.csv'
            if is_file_latest(file_path):
                with open(file_path, 'r') as csvfile:
                    csv_content = csv.reader(csvfile, delimiter=',')
                    entries = []
                    for row in csv_content:
                        # trimmed by -1 because thers is an empty '' field at end
                        entries.append(tuple(row))
                    # removing the first row of the entry because it contains header
                    del entries[0]

                    isin = Stock.objects.get(stock=item, series = 'EQ').isin

                    rows = []
                    prev_close=None
                    log.info('parsing csv file of {} for upload into eod_hist'.format(item))
                    for x in entries:
                        # Date,Open,High,Low,Last,Close,Total Trade Quantity,Turnover (Lacs)
                        if prev_close is not None and x[7]!='':
                            rows.append([item,'EQ', x[1], x[2], x[3], x[4], x[5], prev_close, x[6], float(x[7])*100000, x[0], 0, isin])
                        elif x[7]!='':
                            rows.append([item,'EQ', x[1], x[2], x[3], x[4], x[5], x[5], x[6], float(x[7])*100000, x[0], 0, isin])
                        prev_close = x[5]

                    if len(rows)>0:
                        latest_date=rows[0][10]
                        # log.info('clearing eod_hist table to avoid duplicates:<{}>'.format(item))
                        try:
                            curs_db2.execute('delete from eod_hist where symbol=? and series=? and timestamp<=?',(item,'EQ',latest_date)) # emptying table
                            curs_db2.executemany('INSERT INTO eod_hist VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
                            conn_db2.commit()
                        except Exception as e:
                            log.warn(e)

        except FileNotFoundError as e:
            log.warn('file not found while inserting into eod_hist : {}, exception:{}'.format(item, e))
 
def download_eod_yahoo(stock_set):
    conn_db2 = sqlite3.connect(settings.HIST_DB)
    curs_db2 = conn_db2.cursor()
    stock_set=stock_set
    to_date = datetime.datetime.now()
    print(stock_set)
    
    for item in stock_set:
        try:
            file_path = 'harvest/data/eod_hist_yahoo/NSE-'+item+'.gzip'
            if not is_file_latest(file_path):
                isin = Stock.objects.get(stock=item, series = 'EQ').isin
                data = Fetcher(item+".NS", [int(to_date.year-5),int(to_date.month),int(to_date.day)], [int(to_date.year),int(to_date.month),int(to_date.day)])
                dt = data.getHistorical()
                dt.columns = [c.replace(' ', '_') for c in dt.columns]
                # print(dt)
                # if len(dt.index)==0:
                #     data = Fetcher(item, [to_date.year,to_date.month,to_date.day], [to_date.year-5,to_date.month,to_date.day])
                #     dt = data.getHistorical()
                dt.to_pickle(file_path)
                ls=[]
                prev_close=None
                for row in dt.itertuples():
                    # print(row)
                    if prev_close is not None and row.Open!='null':
                        ls.append([item,'EQ', row.Open, row.High, row.Low, row.Close, row.Close, prev_close, row.Adj_Close, row.Volume,float(row.Volume)*float(row.Close), row.Date, 0, isin])
                    elif row.Open!='null':
                        ls.append([item,'EQ', row.Open, row.High, row.Low, row.Close, row.Close, row.Close, row.Adj_Close, row.Volume,float(row.Volume)*float(row.Close), row.Date, 0, isin])
                    prev_close = row.Close
                log.info('prcessing {} entries from yahoo download for stock:{}'.format(len(ls), item))

                if len(ls)>0:
                    latest_date=ls[0][10]
                    log.info('clearing eod_yahoo table to avoid duplicates:<{}>'.format(item))
                    try:
                        curs_db2.execute('delete from eod_yahoo where symbol=? and series=? and timestamp<=?',(item,'EQ',latest_date)) # emptying table
                        curs_db2.executemany('INSERT INTO eod_yahoo VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', ls)
                        conn_db2.commit()
                    except Exception as e:
                        log.warn(e)
            else:
                log.debug('skipping eod yahoo history download for stock:%s',item)

        
            #return None # to skip loop after first iteration
        except Exception as e:
            log.warn('exception occurred while downloading eod data from yahoo for:{}, erro:{}'.format(item,e))
            print(e)
          

def download_eod_hist():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('select distinct stock from harvest_stock where series="EQ" order by stock')
    stock = []
    for row in c:
        stock.append(row[0])
    
    stock_set = stock
    
    # for i in stock_set:
    #     url = 'https://www.quandl.com/api/v3/datasets/NSE/'+urllib.parse.quote_plus(i)+'.csv?api_key='+api_key+'&limit=1095'
    #     dest = 'harvest/data/eod_hist/NSE-'+i+'.csv'

    #     if os.path.exists(dest) and is_file_latest(dest):
    #         log.debug('skipping eod history download for stock:%s',i)
    #     else:
    #         try:            
    #             urllib.request.urlretrieve(url, dest)
    #             log.info('>downloaded  3 year eod  for %s',i)
    #         except Exception as e:
    #             log.error(e)
    #             log.error('Download EOD hist Err: %s',i)
    #             # log.debug(e)
    
    result = {}
    result['success'] = True

    #upload_to_hist_db(stock_set)
    #download_eod_yahoo(stock_set)

    log.info(result)
    print(json.dumps(result))

execute = download_eod_hist

if __name__ == '__main__':
    # test1.py executed as script
    # do something
    execute()
