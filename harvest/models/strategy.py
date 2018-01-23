from django.db import models
import uuid

class Stock(models.Model):
    stock = models.CharField(max_length=20)
    series = models.CharField(max_length=2)
    open = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    high = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    low = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    close = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    last = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    prevclose = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    tottrdqty = models.IntegerField(default=0)
    tottrdval = models.DecimalField(max_digits=20, default=0, decimal_places=2)
    timestamp = models.DateField()
    totaltrades = models.IntegerField(default=0)
    isin = models.CharField(max_length=20, primary_key=True)
    def __str__(self):
        return self.isin+'__'+self.stock+'__'+str(self.close)

    class meta:
        unique_together = ('stock', 'series', 'isin')

class Strategy(models.Model):
    status_choices = (("ACTIVE", "ACTIVE"), ("INACTIVE", "INACTIVE"))
    close_choices = (("SELL","SELL"),("BUY","BUY"))
    name = models.CharField(max_length=20)
    status = models.CharField(
        max_length=10, choices=status_choices, default="INACTIVE")
    stocks = models.ManyToManyField(Stock, through='Watchlist')
    close_type = models.CharField(
        max_length=10, choices=close_choices, default="SELL")
    def __str__(self):
        return self.name+'__'+self.status

class Watchlist(models.Model):
    status_choices = (("ACTIVE", "ACTIVE"), ("INACTIVE",
                                             "INACTIVE"), ("FLUSH", "FLUSH"))
    signal_status_choices = (("OPEN", "OPEN"),("CLOSE", "CLOSE"))
    
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    norm_score = models.DecimalField(default=0, decimal_places=2, max_digits=5)
    score = models.DecimalField(default=0, decimal_places=2, max_digits=5)
    exit = models.DecimalField(default=0, decimal_places=2, max_digits=5)
    train_details = models.TextField(default="")
    last_transact_price = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    last_qty = models.IntegerField(default=0)
    status = models.CharField(
        max_length=10, choices=status_choices, default="INACTIVE")
    signal_status = models.CharField(choices=status_choices, default="CLOSE", max_length=20)
    profit_earned = models.DecimalField(max_digits=20, default=0, decimal_places=2)
    hold_active_days = models.IntegerField(default=0)
    percent_low = models.IntegerField(default=0)
    allocation = models.DecimalField(max_digits=10, default=0, decimal_places=6)
   

    class meta:
        unique_together = ('strategy', 'stock')

    def __str__(self):
        return self.strategy.name+'/'+self.stock.stock+'/'+self.status+'/'+self.signal_status+'__'+str(self.norm_score)+'__'+str(self.score)+'__'+str(self.exit)+'__'+str(self.profit_earned)

class Signal(models.Model):
    status_choices = (("PENDING_OPEN", "PENDING_OPEN"), ("OPEN", "OPEN"),
                      ("PENDING_CLOSE", "PENDING_CLOSE"), ("CLOSE", "CLOSE"))
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE)
    status = models.CharField(choices=status_choices, default="PENDING_OPEN", max_length=20)
    time = models.DateTimeField()
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.watchlist.strategy.name+'/'+self.watchlist.stock.stock+'/'+self.status+'__'+str(self.uuid)



class Order(models.Model):
    status_choices = (("PENDING", "PENDING"), ("COMPLETE", "COMPLETE"),
                      ("FAILED", "FAILED"))
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE)
    status = models.CharField(choices=status_choices, default="PENDING", max_length=20)
    time = models.DateTimeField()
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)

    product = models.CharField(max_length=20)
    qty = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    avg_price = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    order_info = models.CharField(max_length=20)
    remote_status = models.CharField(max_length=20,null=True)
    call = models.CharField(max_length=20, null=True)
    def __str__(self):
        return self.signal.watchlist.strategy.name+'/'+self.signal.watchlist.stock.stock+'/'+self.call+'/'+self.status+'__'+str(self.qty)+'__'+str(self.price)+'__'+str(self.uuid)



class Ledger(models.Model):
    status_choices = (("PENDING_OPEN", "PENDING_OPEN"), ("OPEN", "OPEN"),
                      ("PENDING_CLOSE", "PENDING_CLOSE"), ("CLOSE", "CLOSE"),("NONE", "NONE"))
    opening = models.DecimalField(max_digits=12, default=0, decimal_places=2)
    credit = models.DecimalField(max_digits=12, default=0, decimal_places=2)
    debit = models.DecimalField(max_digits=12, default=0, decimal_places=2)
    closing = models.DecimalField(max_digits=12, default=0, decimal_places=2)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True)
    signal_status = models.CharField(choices=status_choices, default="NONE", max_length=20, null=True)
    
    desc =  models.CharField(max_length=64)
    timestamp = models.DateTimeField()

    def __str__(self):
        return str(self.opening)+'__'+str(self.credit)+'__'+str(self.debit)+'__'+str(self.closing)+'__'+self.desc
    

