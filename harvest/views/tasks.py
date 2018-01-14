from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from harvest.tasks import nse_download

def download_latest_eod(request):
    response = {"success":False}
    response =  nse_download.execute()
    final = JsonResponse(response, safe=False)
    return final
