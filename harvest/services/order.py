import logging
from datetime import datetime
from django.utils import timezone
import logging
import uuid

from django.conf import settings
from harvest.models.strategy import Strategy, Stock, Watchlist, Signal, Order, Ledger
from harvest.services import signal

def place(my_signal, type, quantity, price, **other):
    order_id = str(uuid.uuid4())
    my_order = Order.objects.create(signal=my_signal, 
        status = 'PENDING',
        time=timezone.now(),
        uuid=order_id,
        product='',
        qty=quantity,
        price=price,
        avg_price=0,
        order_info=other,
        remote_status=None,
        call=type
        )
    return my_order

def confirm(order_id, avg_price):
    my_order = Order.objects.get(uuid = order_id)

    if avg_price<=0:
        return {"success": False, "msg":"Avg_price cannot be zero"}

    if my_order.status != 'PENDING':
        return {"success": False, "msg":"Status should be PENDING"}

    if my_order.status == 'PENDING':
        my_order.status = 'COMPLETE'
        my_order.avg_price = avg_price
        my_order.save()

        signal.confirm(my_order, my_order.signal)

    return {"success": True}

def cancel(order_id):
    my_order = Order.objects.get(uuid = order_id)

    if my_order.status != 'PENDING':
        return {"success": False, "msg":"Status should be PENDING"}

    if my_order.status == 'PENDING':
        my_order.status = 'FAILED'
        my_order.save()

        signal.cancel(my_order, my_order.signal)
            
    return {"success": True}