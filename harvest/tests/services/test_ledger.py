import datetime
from unittest import skip
from django.urls import reverse
from django.test import TestCase
from import_export import resources
from tablib import Dataset
import datetime
from django.utils import timezone
import logging
import decimal
log = logging.getLogger(__name__)

from django.conf import settings
from harvest.models.strategy import Strategy, Stock, Watchlist, Ledger, Order, Signal
#import harvest.tests.LogThisTestCase as LogThisTestCase

# class StockResource(resources.ModelResource):
#     class Meta:
#         model = Stock

def create_strategy(strategy_name):
    return Strategy.objects.create(name=strategy_name, status="ACTIVE")

# def add_stocks_to_watchlist(csv_path):
#         #refer: https://simpleisbetterthancomplex.com/packages/2016/08/11/django-import-export.html
#         stock_resource = StockResource()
#         dataset = Dataset()
#         with open(csv_path) as new_stocks:
#         # new_stocks = settings.BASE_DIR+'/harvest/test_data/eod_sample.csv'
#             imported_data = dataset.load(new_stocks.read())
#             stock_resource.import_data(dataset, dry_run=False)  # Actually import now


class Ledger_test(TestCase):

    def setUp(self):
        pass

    @classmethod
    def setUpClass(cls):    #refer: https://stackoverflow.com/a/14306659
        # # populating tables
        # print("populating tables")
        strategy = create_strategy(strategy_name="RISKY52D")
        # add_stocks_to_watchlist(settings.BASE_DIR+ settings.DATA_DIRECTORY+'/eod_sample_1.csv')
        # # Ledger.objects.create(credit=20000, closing=20000,desc="RISKY52D/CASHIN",strategy=strategy, timestamp=timezone.now())
        super(Ledger_test, cls).setUpClass()

    def test_add_entry_to_ledger(self):

        response = self.client.get(reverse('harvest:add_fund', kwargs={'strategy_id': 1, 'amt':'3000.00'}))
        self.assertContains(response, '''"success": true''')

        log.info("\n ======== Ledger ========")
        for item in Ledger.objects.filter(strategy__name='RISKY52D'):
            log.info(item)


        response = self.client.get(reverse('harvest:pull_fund', kwargs={'strategy_id': 1, 'amt':'1000.00'}))
        self.assertContains(response, '''"success": true''')

        response = self.client.get(reverse('harvest:pull_fund', kwargs={'strategy_id': 1, 'amt':'3000.00'}))
        self.assertContains(response, '''"success": false''')


        log.info("\n ======== Ledger ========")
        for item in Ledger.objects.filter(strategy__name='RISKY52D'):
            log.info(item)

    
