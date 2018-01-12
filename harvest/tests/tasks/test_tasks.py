import datetime
from unittest import skip
from django.urls import reverse
from django.test import TestCase
from import_export import resources
from tablib import Dataset
import datetime
from django.utils import timezone
import logging
log = logging.getLogger(__name__)

from django.conf import settings
from harvest.models.strategy import Strategy, Stock, Watchlist, Ledger, Order, Signal
from harvest.tasks import nse_download

def create_strategy(strategy_name):
    return Strategy.objects.create(name=strategy_name, status="ACTIVE")

# def add_stocks_to_watchlist():
#         #refer: https://simpleisbetterthancomplex.com/packages/2016/08/11/django-import-export.html
#         stock_resource = StockResource()
#         dataset = Dataset()
#         path = settings.BASE_DIR+ settings.DATA_DIRECTORY+'/eod_sample.csv'
#         with open(path) as new_stocks:
#         # new_stocks = settings.BASE_DIR+'/harvest/test_data/eod_sample.csv'
#             imported_data = dataset.load(new_stocks.read())
#             stock_resource.import_data(dataset, dry_run=False)  # Actually import now


class Tasks(TestCase):

    def setUp(self):
        pass

    @classmethod
    def setUpClass(cls):    #refer: https://stackoverflow.com/a/14306659
        # populating tables
        # print("populating tables")
        # strategy = create_strategy(strategy_name="RISKY52D")
        # add_stocks_to_watchlist()
        # Ledger.objects.create(credit=10000, closing=10000,desc="RISKY52D/CASHIN",strategy=strategy, timestamp=timezone.now())
        super(Tasks, cls).setUpClass()

    #@skip('time consuming')
    def test_nse_download(self):
        nse_download.execute()

