from Naked.toolshed.shell import execute_js
import sqlite3
import datetime
import csv
import copy
from django.core.exceptions import ObjectDoesNotExist

import logging
log = logging.getLogger(__name__)

from django.conf import settings
from harvest.models.strategy import Strategy, Stock, Watchlist, Ledger, Order, Signal


def upload_to_db():
    log.info('task: uploading  daily nse eod data to sqlite')
    # conn_db1 = sqlite3.connect('harvest/../../db/harvest.db')
    conn_db2 = sqlite3.connect(settings.HIST_DB)
    # curs_db1 = conn_db1.cursor()
    curs_db2 = conn_db2.cursor()

    with open('harvest/data/eod_nse/eod_latest.csv', 'r') as csvfile:
        csv_content = csv.reader(csvfile, delimiter=',')
        entries = []
        for row in csv_content:
            # trimmed by -1 because thers is an empty '' field at end
            entries.append(list(row[:-1]))
        # removing the first row of the entry because it contains header
        del entries[0]

        for row in entries:
            row[10] = datetime.datetime.strptime(row[10] ,'%d-%b-%Y').strftime('%Y-%m-%d')

        entries2 =  copy.deepcopy(entries)
        for row in entries2:
            row.insert(8,row[5])

        log.info('clearing table to avoid duplicates:<{}>'.format(entries[0][10]))
        curs_db2.execute('delete from eod_hist where timestamp like ?',("%"+entries[0][10]+"%",)) # emptying table
        curs_db2.executemany('INSERT INTO eod_hist VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', entries)
        conn_db2.commit()

        log.info('clearing table to avoid duplicates:<{}>'.format(entries[0][10]))
        curs_db2.execute('delete from eod_yahoo where timestamp like ?',("%"+entries[0][10]+"%",)) # emptying table
        curs_db2.executemany('INSERT INTO eod_yahoo VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', entries2)
        conn_db2.commit()

        count = 0
        for item in entries:
            try:
                stk = Stock.objects.get(stock=item[0], series = item[1])
                if stk is not None:
                    timestamp = item[10]
                    stk.open = item[2]
                    stk.high = item[3]
                    stk.low = item[4] 
                    stk.close = item[5] 
                    stk.last = item[6] 
                    stk.prevclose = item[7]
                    stk.tottrdqty = item[8]
                    stk.tottrdval = item[9]
                    stk.timestamp = timestamp 
                    stk.totaltrades = item[11] 
                    stk.save()
                else:
                    log.warn('stock entry not found while updating latest eod : {}'.format(item[0]))

            except ObjectDoesNotExist as e:
                log.warn('{} -->  {}'.format(e ,str(item)))
                Stock.objects.create(
                        stock=item[0], 
                        series = item[1],
                        open = item[2],
                        high = item[3],
                        low = item[4], 
                        close = item[5], 
                        last = item[6], 
                        prevclose = item[7],
                        tottrdqty = item[8],
                        tottrdval = item[9],
                        timestamp = item[10], 
                        totaltrades = item[11],
                        isin= item[12] 
                        )
                count= count +1

        print('tot obj not found: {}, total_objects tried:{}',count,len(entries))
            

def execute():
    success = execute_js('harvest/nodejs/download_nse.js')
    if success:
        log.info('download success')
        upload_to_db()
        return {"success":True}
    else:
        log.info('download failed')
        return {"success":False, 'msg':'download failed'}


if __name__ == '__main__':
    execute()
