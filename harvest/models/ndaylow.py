from django.db import models
import uuid

from harvest.models.strategy import Stock, Strategy

class Ndaylow(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    avg_hold_inter = models.DecimalField(default=0, decimal_places=2, max_digits=5)
    avg_trade_val = models.DecimalField(max_digits=20, default=0, decimal_places=2)
    avg_hold_inter = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    margin = models.DecimalField(max_digits=10, default=0, decimal_places=2)
    n_day_low = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)
    profit = models.DecimalField(max_digits=20, default=0, decimal_places=2)
    return_per_day = models.DecimalField(max_digits=20, default=0, decimal_places=2)
    score =models.DecimalField(max_digits=10, default=0, decimal_places=6)
    norm_score =models.DecimalField(max_digits=10, default=0, decimal_places=6)
    allocation = models.DecimalField(max_digits=10, default=0, decimal_places=6)
    # percent_low = models.IntegerField(default=0)
    def __str__(self):
        return self.strategy.name+'/'+self.stock.stock+'/'+str(self.norm_score)+'__'+str(self.allocation)

    class meta:
        unique_together = ('stock', 'strategy')
