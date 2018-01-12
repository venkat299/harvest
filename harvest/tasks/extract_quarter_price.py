""" downloads eod history for the stocks available from NSE website """
import os.path
import datetime
import sys
import argparse
# import pyexcel as pe
import configparser 
import os
import json
import csv
import quandl
import pandas as pd
import sqlite3
import urllib.request
import urllib.parse
import logging
log = logging.getLogger(__name__)

# dbpath = settings.BASE_DIR+'/'+settings.HIST_DB
dbpath = './harvest_hist.db'


def get_qtr_price(symbol, period_id, year, date=None):
    q_map = {}
    q_map['date'] =  date
    q_map['q4'] =  str(int(year)+1)+'-04-01'
    q_map['q1'] =  year+'-07-01'
    q_map['q2'] =  year+'-10-01'
    q_map['q3'] =  str(int(year)+1)+'-01-01'
    period = q_map[period_id]
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    c.execute(''' SELECT adj_close, timestamp
                    FROM eod_yahoo
                    WHERE symbol = ? AND 
                        series = 'EQ'
                        and timestamp between date(?,'-45 days') and date(?,'+30 days')
                    ORDER BY timestamp ;
            ''',(symbol, period, period))
    ls = []
    for row in c:
        ls.append(row)

    size = len(ls)

    print(size)

    dates = []
    dates.append(('-1.5m',0))
    dates.append(('  -1m',10))
    dates.append(('  -2w',20))
    dates.append(('  -1w',25))
    dates.append(('    0',30))
    dates.append(('  +1w',size-1-15))
    dates.append(('  +2w',size-1-10))
    dates.append(('  +1m',size-1))



    res=[]

    for x in dates:
        try:
            val = round(ls[x[1]][0])
            res.append( (x[0], val) )
        except IndexError as e:
            print(e)
            res.append((x[0], '-'))
            

    for item  in res:
        print(item)

    for item in res:
            print((item[1]))
        
        
    
    # s = ''
    # for item  in res:
    #     s = s+ str(round((item[1][0]),1))+',' 
    # print(s)


execute = get_qtr_price

if __name__ == '__main__':
    # test1.py executed as script
    parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     'filename', metavar='int', type=int, choices=range(10),
    #      nargs='+', help='give a file name')
    parser.add_argument('symbol',  help='symbol')
    parser.add_argument('period_id',  help='option=q1,q2,q3,q4')
    parser.add_argument('year',  help='YYYY format')
    parser.add_argument('date',  help='YYYY format')
    args = parser.parse_args()
    print(args)
    execute(args.symbol, args.period_id, args.year)
