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
#import harvest.tests.LogThisTestCase as LogThisTestCase

class StockResource(resources.ModelResource):
    class Meta:
        model = Stock

def create_strategy(strategy_name):
    return Strategy.objects.create(name=strategy_name, status="ACTIVE")

def add_stocks_to_watchlist(csv_path):
        #refer: https://simpleisbetterthancomplex.com/packages/2016/08/11/django-import-export.html
        stock_resource = StockResource()
        dataset = Dataset()
        with open(csv_path) as new_stocks:
        # new_stocks = settings.BASE_DIR+'/harvest/test_data/eod_sample.csv'
            imported_data = dataset.load(new_stocks.read())
            stock_resource.import_data(dataset, dry_run=False)  # Actually import now


class Risky52D(TestCase):

    def setUp(self):
        pass

    @classmethod
    def setUpClass(cls):    #refer: https://stackoverflow.com/a/14306659
        # populating tables
        print("populating tables")
        strategy = create_strategy(strategy_name="RISKY52D")
        add_stocks_to_watchlist(settings.BASE_DIR+ settings.DATA_DIRECTORY+'/eod_sample_1.csv')
        Ledger.objects.create(credit=20000, closing=20000,desc="RISKY52D/CASHIN",strategy=strategy, timestamp=timezone.now())
        super(Risky52D, cls).setUpClass()

    def test_strategy_view_with_an_entry(self):
        """
        test the web page for strategy
        """
        response = self.client.get(reverse('harvest:strategy'))
        self.assertQuerysetEqual(
            response.context['user_strategy_list'],
            ['<Strategy: RISKY52D__ACTIVE>']
        )
        self.assertContains(response, '''>RISKY52D</a>
            </td>
            <td>ACTIVE</td>''')


    @skip('time consuming')
    def test_train_strategy(self):

        # test train()
        response = self.client.get(reverse('harvest:strategy_train', kwargs={'strategy_id': 1}))
        self.assertContains(response, '''"success": true''')
        log.info("\n ======== Watchlist ========")
        for item in Watchlist.objects.filter(strategy__name='RISKY52D'):
            log.info(item)


    # @skip('time consuming')
    def test_strategy_api(self):

        # test train()
        response = self.client.get(reverse('harvest:strategy_train', kwargs={'strategy_id': 1}))
        self.assertContains(response, '''"success": true''')

        # test execute()
        response = self.client.get(reverse('harvest:strategy_predict', kwargs={'strategy_id': 1}))
        self.assertContains(response, '''"success": true''')


        log.info("\n ======== Watchlist ========")
        for item in Watchlist.objects.filter(strategy__name='RISKY52D'):
            log.info(item)

        log.info("\n ======== Signals ========")
        for item in Signal.objects.filter(watchlist__strategy__name='RISKY52D'):
            log.info(item)


        order =Order.objects.get(signal__watchlist__strategy__name='RISKY52D', signal__watchlist__stock__stock='3IINFOTECH', status='PENDING')
        uuid = order.uuid
        avg_price = order.price
        response = self.client.get(reverse('harvest:strategy_confirm_order', kwargs={'uuid': uuid, 'avg_price':avg_price}))
        self.assertContains(response, '''"success": true''')

        order =Order.objects.get(signal__watchlist__strategy__name='RISKY52D', signal__watchlist__stock__stock='ASHOKLEY', status='PENDING')
        uuid = order.uuid
        avg_price = order.price
        response = self.client.get(reverse('harvest:strategy_confirm_order', kwargs={'uuid': uuid, 'avg_price':avg_price}))
        self.assertContains(response, '''"success": true''')

        uuid = Order.objects.get(signal__watchlist__strategy__name='RISKY52D', signal__watchlist__stock__stock='DABUR', status='PENDING').uuid
        response = self.client.get(reverse('harvest:strategy_cancel_order', kwargs={'uuid': uuid}))
        self.assertContains(response, '''"success": true''')

        stock_1 = Stock.objects.get(stock='3IINFOTECH', series='EQ')
        stock_1.close = 2500
        stock_1.save()
        stock_2 = Stock.objects.get(stock='ASHOKLEY', series='EQ')
        stock_2.close = 150
        stock_2.save()

        response = self.client.get(reverse('harvest:strategy_predict', kwargs={'strategy_id': 1}))
        self.assertContains(response, '''"success": true''')

        order =Order.objects.get(signal__watchlist__strategy__name='RISKY52D', signal__watchlist__stock__stock='ASHOKLEY', status='PENDING')
        uuid = order.uuid
        avg_price = order.price
        response = self.client.get(reverse('harvest:strategy_confirm_order', kwargs={'uuid': uuid, 'avg_price':avg_price}))
        self.assertContains(response, '''"success": true''')

        uuid = Order.objects.get(signal__watchlist__strategy__name='RISKY52D', signal__watchlist__stock__stock='3IINFOTECH', status='PENDING').uuid
        response = self.client.get(reverse('harvest:strategy_cancel_order', kwargs={'uuid': uuid}))
        self.assertContains(response, '''"success": true''')

        #prematurly closing a signal 
        watchlist_id1= Watchlist.objects.get(stock=stock_1, strategy__name='RISKY52D').id
        response = self.client.get(reverse('harvest:close_signal', kwargs={'watchlist_id': watchlist_id1}))
        self.assertContains(response, '''"success": true''')

        log.info("\n ======== Watchlist ========")
        for item in Watchlist.objects.filter(strategy__name='RISKY52D'):
            log.info(item)

        log.info("\n ======== Signals ========")
        for item in Signal.objects.filter(watchlist__strategy__name='RISKY52D'):
            log.info(item)

        log.info("\n ======== Order ========")
        for item in Order.objects.filter(signal__watchlist__strategy__name='RISKY52D'):
            log.info(item)

        log.info("\n ======== Ledger ========")
        for item in Ledger.objects.filter(strategy__name='RISKY52D'):
            log.info(item)

    
