import json
import boto3
import bcrypt
import decimal
from pprint import pprint
from django.http import HttpResponse
from boto3.dynamodb.conditions import Key
from l import Worker

def replace_decimals(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = replace_decimals(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = replace_decimals(obj[k])
        return obj
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

def prepObj(obj):
    return HttpResponse(json.dumps(replace_decimals(obj)))

def index(request):
    return HttpResponse(json.dumps({
    	'status':200
    }))

x = Worker()

def addDriver(request):
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    origin = (float(obj['origin_latitude']), float(obj['origin_longitude']))
    destination = (float(obj['destination_latitude']), float(obj['destination_longitude']))
    t = x.insertDriver(origin, destination)
    return prepObj({'index':t})

def addItem(request):
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    index = obj['index']
    origin = (float(obj['origin_latitude']), float(obj['origin_longitude']))
    destination = (float(obj['destination_latitude']), float(obj['destination_longitude']))
    pprint(obj)
    print(origin)
    print(destination)
    x.insertItems(origin, destination, index)
    return prepObj({})
