import json
import boto3
import bcrypt
import decimal
from pprint import pprint
from django.http import HttpResponse
from boto3.dynamodb.conditions import Key
dynamodb = boto3.resource('dynamodb','ap-southeast-1')
usersTable = dynamodb.Table('LifeHack2021-users')
donationsTable = dynamodb.Table('LifeHack2021-donations')

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

def getPriorityUsers(request):
    recipients = []
    x = usersTable.scan()['Items']
    recipients = [item['username'] for item in x if item['role'] == 'recipient']
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    index = int(obj['index'])

    toReturn = [
        'r','r2','r3','r4','r5'
    ]

    for i in toReturn:
        userInfo =  usersTable.query(
            KeyConditionExpression = Key('username').eq(i)    
        )['Items'][0]
        if index in userInfo['priorityItems']:
            print("DONE")
        else:
            userInfo['priorityItems'].append(index)
            usersTable.update_item(
                Key = {'username':userInfo['username']},
                UpdateExpression = f'set priorityItems = :a',
                ExpressionAttributeValues = {':a': userInfo['priorityItems']}
            )

    return HttpResponse(json.dumps(
        toReturn
    ))

