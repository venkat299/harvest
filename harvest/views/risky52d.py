from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from harvest.services.risky52d.main import  Risky52D
from harvest.services import order

def reload_watchlist(request):
    response = {"success":False}
    response = Risky52D.load_into_watchlist()
    final = JsonResponse(response, safe=False)
    return final
