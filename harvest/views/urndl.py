from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from harvest.services.urndl.main import  URNDL
from harvest.services import order

def reload_watchlist(request):
    response = {"success":False}
    response = URNDL.load_into_watchlist()
    final = JsonResponse(response, safe=False)
    return final
