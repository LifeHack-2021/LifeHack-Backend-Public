from django.shortcuts import render
from django.shortcuts import render
import base64
import uuid
import sys
import json
import boto3
import decimal
import datetime
from boto3.dynamodb.conditions import Key
from PIL import Image
from io import BytesIO
from pprint import pprint
from django.http import HttpResponse
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb','ap-southeast-1')
storiesTable = dynamodb.Table('LifeHack2021-stories')

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

def createStory(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    id = str(uuid.uuid4())

    dynamoObj = {
        'id': id,
        'donor': obj['donor'],
        'recipient' : obj['recipient'],
        'dateCreated': datetime.datetime.now().strftime("%Y-%m-%d %X"),
        'title': obj['title'],
        'description': obj['description']
    }

    dynamoObj['imageLink'] = f'https://lifehack2021-stories.s3.ap-southeast-1.amazonaws.com/{str(id)}.png'

    img = obj['image']
    im = Image.open(BytesIO(base64.b64decode(img)))
    im.save('tmp.png', 'PNG')

    s3.upload_file('tmp.png','lifehack2021-stories',f'{id}.png', ExtraArgs={"ACL": 'public-read'})
    storiesTable.put_item(Item=dynamoObj)

    return prepObj(dynamoObj)

def getAllStories(request):
    if request.method != 'GET':
        return HttpResponse(json.dumps({'status':300}))

    items = storiesTable.scan()['Items']
    return prepObj(items)

def getStoriesByUser(request, username):
    if request.method != 'GET':
        return HttpResponse(json.dumps({'status':300}))

    items = storiesTable.scan()['Items']
    items = [i for i in items if i['donor'] == username]
    return prepObj(items)

