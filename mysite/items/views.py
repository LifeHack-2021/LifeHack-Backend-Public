from django.shortcuts import render
import base64
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

def exists(index):
    response = donationsTable.query(
        KeyConditionExpression = Key('index').eq(index)
    )
    value = response['Items']
    if len(value) != 1:
        return False
    return True
        
def createNewItem(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))

    try:
        dynamoObj = {
            'index':0,
            'donor':obj['donor'],
            'recipient':'none',
            'description':obj['description'],
            'saleDate': datetime.datetime.now().strftime("%Y-%m-%d %X"),
            'purchaseDate': 'none',
            'title': obj['title'],
            'category': obj['category'],
            'depositIDarea': 'none',
            'status': 'available',
            'story': '',
            'storyTitle': '',
            'rating': -1,
            'priority':0
        }

        with open('items/id.txt','r') as f:
           id = f.read()
           id = int(id)
           dynamoObj['index'] = id

        with open('items/id.txt','w') as f:
            f.write(str(dynamoObj['index']+1))

        dynamoObj['imageLink'] = f'https://lifehack2021-images.s3.ap-southeast-1.amazonaws.com/{str(id)}.png'

        img = obj['image']
        im = Image.open(BytesIO(base64.b64decode(img)))
        im.save('tmp.png', 'PNG')

        s3.upload_file('tmp.png','lifehack2021-images',f'{id}.png', ExtraArgs={"ACL": 'public-read'}) 

        pprint(dynamoObj)

        donationsTable.put_item(Item = dynamoObj) 
        
        return prepObj(dynamoObj)
    except:
        e = sys.exc_info()
        return HttpResponse(json.dumps({
            'status':300,
            'error':str(e)
        }))

def getAllItems(request):
    if request.method != 'GET':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    items = donationsTable.scan()['Items']
    items = [i for i in items if i['status'] != 'wishlist']
    return prepObj(items)

def editStory(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    try: 
        body = request.body
        obj = json.loads(body.decode('utf-8').replace("'", '"'))
        if not exists(obj['index']):
            return HttpResponse(json.dumps({'status':300,'error':'Invalid Item'}))

        donationsTable.update_item(
            Key = {'index':obj['index']},
            UpdateExpression = f'set story = :a, storyTitle = :b',
            ExpressionAttributeValues = {':a': obj['story'], ':b':obj['storyTitle']}
        )
        response = donationsTable.query(
            KeyConditionExpression = Key('index').eq(obj['index'])
        )

        value = response['Items'][0]

        return prepObj(value)
    except:
        e = sys.exc_info()
        return HttpResponse(json.dumps({
            'status':300,
            'error':str(e)
        }))

def editStatus(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    try: 
        body = request.body
        obj = json.loads(body.decode('utf-8').replace("'", '"'))
        if not exists(obj['index']):
            return HttpResponse(json.dumps({'status':300,'error':'Invalid Item'}))
        
        if obj['status'] not in ['available', 'redeemed', 'in transit', 'at collection', 'received', 'wishlist']:
            return HttpResponse(json.dumps({'status':300,'error':'Invalid Status'}))

        donationsTable.update_item(
            Key = {'index':obj['index']},
            UpdateExpression = f'set #a = :a',
            ExpressionAttributeValues = {':a': obj['status']},
            ExpressionAttributeNames = {'#a': 'status'} 
        )

        response = donationsTable.query(
            KeyConditionExpression = Key('index').eq(obj['index'])
        )

        value = response['Items'][0]

        return prepObj(value)
    except:
        e = sys.exc_info()
        return HttpResponse(json.dumps({
            'status':300,
            'error':str(e)
        }))

def getAllStories(request):
    if request.method != 'GET':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    items = donationsTable.scan()['Items']
    stories = [item for item in items if item['story'] != '']
    return prepObj(stories)

def getPendingItems(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    items = donationsTable.scan()['Items']
    items = [item for item in items if item['status'] not in ['available', 'received', 'wishlist']]
    items = [item for item in items if item ['recipient'] == obj['username']]
    return prepObj(items)

def getItem (request, index):
    if request.method != 'GET':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    index = int(index)
    response = donationsTable.query(
        KeyConditionExpression = Key('index').eq(index)
    )
    value = response['Items']
    if len(value) != 1:
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Index'}))
    value = value[0]
    return prepObj(value)

def deleteItem(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    index = int(obj['index'])
    response = donationsTable.query(
        KeyConditionExpression = Key('index').eq(index)
    )
    value = response['Items']
    if len(value) != 1:
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Index'}))
    value = value[0]

    response = donationsTable.delete_item(
            Key = {'index':index}
    )
    return HttpResponse(json.dumps({'status':200}))

def createWish(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    dynamoObj = {
        'index':0,
        'donor':'none',
        'recipient':obj['recipient'],
        'description':obj['description'],
        'saleDate': datetime.datetime.now().strftime("%Y-%m-%d %X"),
        'purchaseDate': 'none',
        'title': obj['title'],
        'category': obj['category'],
        'depositIDarea': 'none',
        'status': 'wishlist',
        'story': '',
        'storyTitle': '',
        'rating': -1,
        'priority': 1
    }

    with open('items/id.txt','r') as f:
        id = f.read()
        id = int(id)
        dynamoObj['index'] = id

    with open('items/id.txt','w') as f:
         f.write(str(dynamoObj['index']+1))

    dynamoObj['imageLink'] = 'none'

    pprint(dynamoObj)

    donationsTable.put_item(Item = dynamoObj) 
    return prepObj(dynamoObj)

def getWishlist(request, username):
    if request.method != 'GET':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    items = donationsTable.scan()['Items']
    items = [item for item in items if item['status'] == 'wishlist']
    items = [item for item in items if item ['recipient'] == username]
    return prepObj(items)

def setRecipient(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    
    if not exists(obj['index']):
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Item'}))
    index = obj['index']
    recipient = obj['recipient']

    try:
        donationsTable.update_item(
            Key = {'index':index},
            UpdateExpression = f'set recipient = :a',
            ExpressionAttributeValues={':a':recipient},
        )
        return HttpResponse(json.dumps({
            'status':200
        }))
    except:
        e = sys.exc_info()
        return HttpResponse(json.dumps({
            'status':300,
            'error':str(e)
        }))

def setRating(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    if not exists(obj['index']):
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Item'}))
    
    index = obj['index']
    rating = int(obj['rating'])

    if not (0 <= rating and rating <= 100):
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Rating'}))

    try:
        donationsTable.update_item(
            Key = {'index':index},
            UpdateExpression = f'set rating= :a',
            ExpressionAttributeValues={':a':rating},
        )
        return HttpResponse(json.dumps({
            'status':200
        }))
    except:
        e = sys.exc_info()
        return HttpResponse(json.dumps({
            'status':300,
            'error':str(e)
    }))

def getRatings(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    items = donationsTable.scan()['Items']
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    username = obj['username']
    pprint(items)
    items = [item for item in items if item['recipient'] == username]
    items = [item for item in items if item['rating'] != -1]
    return prepObj(items)

def getRecipientItems(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    items = donationsTable.scan()['Items']
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    username = obj['username']
    items = [item for item in items if item['recipient'] == username]
    return prepObj(items)

def getDonorItems(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    items = donationsTable.scan()['Items']
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    username = obj['username']
    items = [item for item in items if item['donor'] == username]
    return prepObj(items)

def editPriority(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    index = int(obj['index'])
    priority = int(obj['priority'])
    if not exists(obj['index']):
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Item'}))
    response = donationsTable.query(
        KeyConditionExpression = Key('index').eq(index)
    )
    value = response['Items']
    if value[0]['status'] != 'wishlist':
        return HttpResponse(json.dumps({'status':300,'error':'Item is not wishlisted'}))

    donationsTable.update_item(
        Key = {'index':index},
        UpdateExpression = f'set priority = :a',
        ExpressionAttributeValues = {':a': priority}
    )
    return HttpResponse(json.dumps({'status':200}))

def tmp():
    ind = []
    for i in donationsTable.scan()['Items']:
        ind.append(i['index'])
    
    for index in ind:
        donationsTable.update_item(
            Key = {'index':index},
            UpdateExpression = f'set priority = :a',
            ExpressionAttributeValues = {':a': 0}
        )

