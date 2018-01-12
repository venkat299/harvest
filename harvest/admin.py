from django.contrib import admin

from .models.strategy import Strategy, Stock, Watchlist
from .models.ndaylow import Ndaylow

admin.site.register(Strategy)
admin.site.register(Stock)
admin.site.register(Watchlist)