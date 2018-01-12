from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from harvest.services.risky52d.main import  Risky52D
from harvest.services import order

def train(request, strategy_id):
    response = {"success":False}

    if strategy_id is "1":
        response = Risky52D.train()

    final = JsonResponse(response, safe=False)
    print(final)
    return final

def predict(request, strategy_id):
    response = {"success":False}

    if strategy_id is "1":
        response = Risky52D.predict()

    final = JsonResponse(response, safe=False)
    return final

def reset(request, strategy_id):
    response = {"success":False}

    if strategy_id is "1":
        response = Risky52D.reset()

    final = JsonResponse(response, safe=False)
    return final


def confirm_order(request, uuid, avg_price):
    response = order.confirm(uuid, float(avg_price))
    # print(response)
    return JsonResponse(response,  safe=False)

def cancel_order(request, uuid):
    return JsonResponse(order.cancel(uuid),  safe=False)
