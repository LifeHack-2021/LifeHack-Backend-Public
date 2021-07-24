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

def createRecipient(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    userObject = {
        'username' : '',
        'password' : '',
        'creditRating' : 50,
        'role': 'recipient',
        'name' : '',
        'userToken': '',
        'priorityItems': [],
        'backstory': ''
    }
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    userObject['username'] = obj['username']
    userObject['name'] = obj['name']
    userObject['userToken'] = obj['userToken']
    password = obj['password']
    hashedPW = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    userObject['password'] = hashedPW
    userObject['password'] = userObject['password'].decode('utf-8')
    usersTable.put_item(Item = userObject)

    userObject.pop('password')
    return prepObj(userObject)

def createDonor(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    userObject = {
        'username' : '',
        'password' : '',
        'creditRating' : 50,
        'role': 'donor',
        'name':'',
        'userToken': '',
        'priorityItems': [],
        'backstory' : ''
    }
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    userObject['username'] = obj['username']
    userObject['name'] = obj['name']
    userObject['userToken'] = obj['userToken']
    password = obj['password']
    hashedPW = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    userObject['password'] = hashedPW
    userObject['password'] = userObject['password'].decode('utf-8')
    usersTable.put_item(Item = userObject)

    userObject.pop('password')
    return prepObj(userObject)

def authLogin(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    obj = {
        'authenticated': 0,
        'userInfo': {}
    }
    body = request.body
    query_obj = json.loads(body.decode('utf-8').replace("'", '"'))
    username = query_obj['username']
    password = query_obj['password']

    response = usersTable.query(
        KeyConditionExpression = Key('username').eq(username)    
    )
    if len(response['Items']) != 1:
        return HttpResponse(json.dumps({'status':300, 'error': 'Invalid User'}))
    
    userInfo = response['Items'][0]
    userInfo['password'] = userInfo['password'].encode('utf-8')

    auth = bcrypt.checkpw(password.encode(), userInfo['password'])
    if not auth:
        return HttpResponse(json.dumps(obj))
    else:
        userInfo.pop('password')
        userInfo['creditRating'] = getCreditRating(userInfo['username'])
        obj['userInfo'] = userInfo
        obj['authenticated'] = 1
        return prepObj(obj)

def getCreditRating(username):
    total = 50
    count = 1
    items = donationsTable.scan()['Items']
    for i in items:
        i['index'] = int(i['index'])
        i['rating'] = int(i['rating'])
    items = [item for item in items if item['donor'] == username]
    for item in items:
        if item['rating'] == -1:
            continue
        total += item['rating']
        count += 1
    return int(total/count)

def getRecommendedItems(request, username):
    if request.method != 'GET':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))

    response = usersTable.query(
        KeyConditionExpression = Key('username').eq(username)
    )

    if len(response['Items']) != 1:
        return HttpResponse(json.dumps({'status':300, 'error': 'Invalid User'}))

    userInfo = replace_decimals(response['Items'][0])
    filteredItems = []
    items = userInfo['priorityItems']

    for i in items:
        if (type(i) != int): continue
        response = donationsTable.query(
            KeyConditionExpression = Key('index').eq(i)
        )['Items']
        if len(response) != 1:
            continue
        item = response[0]
        if item['status'] != 'available':
            continue
        filteredItems.append(item)
    return prepObj(filteredItems)

def getUserInfo(request, username):
    if request.method != 'GET':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))

    response = usersTable.query(
        KeyConditionExpression = Key('username').eq(username)
    )
    if len(response['Items']) != 1:
        return HttpResponse(json.dumps({'status':300, 'error': 'Invalid User'}))

    userInfo = response['Items'][0]
    userInfo.pop('password')
    userInfo['creditRating'] = getCreditRating(username)
    userInfo.pop('priorityItems')
    return prepObj(userInfo)

def tmp():
    ind = []
    for i in usersTable.scan()['Items']:
        i.pop('usersToken')
        ind.append(i)
    
    for i in ind:
        usersTable.put_item(Item = i)

def editStatus(index,status):
    donationsTable.update_item(
        Key = {'index':index},
        UpdateExpression = f'set #a = :a',
        ExpressionAttributeValues = {':a': status},
        ExpressionAttributeNames = {'#a': 'status'}
    )

def editRecipient(index, recipient):
    donationsTable.update_item(
        Key = {'index':index},
        UpdateExpression = f'set recipient = :a',
        ExpressionAttributeValues={':a':recipient},
    )

def rejectItem(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    username = obj['username']
    index = obj['index']
    response = usersTable.query(
        KeyConditionExpression = Key('username').eq(username)
    )
    if len(response['Items']) != 1:
        return HttpResponse(json.dumps({'status':300, 'error': 'Invalid User'}))
    userInfo = response['Items'][0]
    items = [i for i in userInfo['priorityItems'] if i != index]
    if len(items) == len(userInfo['priorityItems']):
        return HttpResponse(json.dumps({'status':300, 'error': 'Invalid Index'}))

    usersTable.update_item(
        Key = {'username':username},
        UpdateExpression = f'set priorityItems = :a',
        ExpressionAttributeValues = {':a': items}
    )
    
    return prepObj({
        'status':200
    })

def acceptItem(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    username = obj['username']
    index = obj['index']
    response = usersTable.query(
        KeyConditionExpression = Key('username').eq(username)
    )
    if len(response['Items']) != 1:
        return HttpResponse(json.dumps({'status':300, 'error': 'Invalid User'}))
    userInfo = response['Items'][0]
    items = [i for i in userInfo['priorityItems'] if i != index]
    if len(items) == len(userInfo['priorityItems']):
        return HttpResponse(json.dumps({'status':300, 'error': 'Invalid Index'}))

    
    usersTable.update_item(
        Key = {'username':username},
        UpdateExpression = f'set priorityItems = :a',
        ExpressionAttributeValues = {':a': items}
    )
    
    editRecipient(index,username)
    editStatus(index,'redeemed')
    
    return prepObj({
        'status':200
    })

def editBackstory(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'status':300,'error':'Invalid Request'}))
    body = request.body
    obj = json.loads(body.decode('utf-8').replace("'", '"'))
    username = obj['username']
    backstory = obj['backstory']
      
    usersTable.update_item(
        Key = {'username':username},
        UpdateExpression = f'set backstory = :a',
        ExpressionAttributeValues = {':a': backstory}
    )

    return prepObj({'status':200})

def getAllUsersInfo(request):
    items = usersTable.scan()['Items']
    for i in items:
        i.pop('password')
        i.pop('userToken')
    pprint(items)
    return prepObj(items)

if __name__ == '__main__':
    tmp()
