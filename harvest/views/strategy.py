from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from harvest.services.risky52d.main import  Risky52D
from harvest.services.urndl.main import  URNDL
from harvest.services import order
from harvest.models.strategy import Strategy

def train(request, strategy_id):
    strategy_id = int(strategy_id)
    response = {"success":False}
    strategy_name = Strategy.objects.get(id=strategy_id).name
    print(strategy_name)

    if strategy_name == "RISKY52D":
        response = Risky52D.train()
    if strategy_name == "URNDL":
        response = URNDL.train()

    # print(response)
    final = JsonResponse(response, safe=False)
    return final

def predict(request, strategy_id):
    response = {"success":False}
    strategy_id = int(strategy_id)
    strategy_name = Strategy.objects.get(id=strategy_id).name

    if strategy_name == "RISKY52D":
        response = Risky52D.predict()
    if strategy_name == "URNDL":
        response = URNDL.predict()

    # print(response)   
    final = JsonResponse(response, safe=False)
    return final

def reset(request, strategy_id):
    response = {"success":False}
    strategy_id = int(strategy_id)
    strategy_name = Strategy.objects.get(id=strategy_id).name

    if strategy_name == "RISKY52D":
        response = Risky52D.reset()
    if strategy_name == "URNDL":
        response = URNDL.reset()

    final = JsonResponse(response, safe=False)
    return final


def confirm_order(request, uuid, avg_price):
    response = order.confirm(uuid, float(avg_price))
    # print(response)
    return JsonResponse(response,  safe=False)

def cancel_order(request, uuid):
    return JsonResponse(order.cancel(uuid),  safe=False)
