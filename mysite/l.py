from key import API_KEY
import time
import json
import random
import googlemaps
import numpy as np
import pandas as pd
from math import floor, ceil, e
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
from pprint import pprint

gmaps = googlemaps.Client(key=API_KEY)

_A = [10]
for i in range(51):
    _A.append(random.uniform(0.8,1.2) *_A[-1])
    _A[-1] = round(_A[-1])

def randomCoord():
    lngDiff = (104.03050544597075 - 103.63920895308122) / 4
    latDiff = (1.4643992538631734 - 1.2623355324310437) / 4
    lngCoord = latCoord = 0

    if (random.uniform(0,1) <= 0.5):
      lngCoord = random.uniform(0,1) * lngDiff + 103.8198
    else:
      lngCoord = -random.uniform(0,1)* lngDiff + 103.8198

    if random.uniform(0,1) <= 0.5:
        latCoord = random.uniform(0,1) * latDiff + 1.3521
    else:
        latCoord = -random.uniform(0,1)*latDiff + 1.3521

    return (latCoord, lngCoord)
    
# Look up an address with reverse geocoding
coord = randomCoord()

def getDuration(A,B):
    mat = gmaps.distance_matrix(A,B)
    return mat['rows'][0]['elements'][0]['duration']['value']

def extraTime(A,B,C,D):
    # Path 1 is to take from A to B
    # Path 2 is to take from A to C then to D then to B
    path1 = getDuration(A,B)
    path2 = getDuration(A,C) + getDuration(C,D) + getDuration(D,B)
    time.sleep(0.5)
    return path2-path1

def sample(n, C, D):
    # We sample N times, choosing coordinates (A,B) to match with (C,D)
    # In reality, can choose (A,B) from previous data
    # From experimentation, given a random (C,D) the n-sample is approximately 1850 
    minVal = 10000000
    for i in range(2):
        A = randomCoord()
        B = randomCoord()
        minVal = min(minVal, extraTime(A,B,C,D))
    print(minVal)
    return minVal

def timeSeriesModel(A):
    l = len(A)

    class Model():
        def __init__(self, t, param):
            self.model = XGBRegressor(n_estimators=100, max_depth=param)

        def fit(self, a, b):
            self.model.fit(a, b)

        def predict(self, a):
            return self.model.predict(a)

    N = len(A) - 4
    l = len(A)
    A += [1, 1, 1, 1]
    D = pd.DataFrame(np.ones(5*l).reshape(-1, 5),
                             columns=["Today", "1 day", "2 day", "3 day", "4 day"])
    for i in range(4, l+4):
        D["Today"][i-4] = A[i]
        D["1 day"][i-4] = A[i-1]
        D["2 day"][i-4] = A[i-2]
        D["3 day"][i-4] = A[i-3]
        D["4 day"][i-4] = A[i-4]

    df = D
    prediction_data = df.drop([i for i in range(N)])
    train_data = df.drop([N, N+1, N+2, N+3]).sample(frac=1, replace=False)
    x = train_data.drop(["Today"], axis=1).values
    y = train_data["Today"]
    S = StandardScaler()
    S.fit(x.reshape(-1, 1))
    t = S.transform(x.reshape(-1,1))
    x = t.reshape(-1,4)
    
    train_set_x = x[0:floor(N*0.8)]
    test_set_x = x[floor(N*0.8):N]
    train_set_y = y.iloc[[i for i in range(0, floor(N*0.8))]]
    test_set_y = y.iloc[[i for i in range(floor(N*0.8), N)]]
    bootstrap_set = df.drop([N, N+1, N+2, N+3])
    err = []

    param = {'max_depth': [2, 3, 4, 5]}
    XGBC = GridSearchCV(XGBRegressor(n_estimators=100), param)
    XGBC.fit(train_set_x, train_set_y)
    mean_test_score = XGBC.cv_results_['mean_test_score']
    r = param['max_depth'][np.argmax(mean_test_score)]

    XGB_model = Model("XGB", r)
    XGB_model.fit(train_set_x, train_set_y)
    E = (XGB_model.predict(test_set_x) - test_set_y).values
    E = E.reshape(1, -1)

    model = Model('XGB',r) 
    model.fit(x, y)
    x_test = S.transform(
        prediction_data.iloc[0].values[1:].reshape(-1, 1)).reshape(1, -1)
    x_next = S.transform(
        prediction_data.iloc[1].values[1:].reshape(-1, 1)).reshape(1, -1)
    pred = model.predict(x_test)
    only_one_forward_pred = pred
    x_next[0][0] = S.transform(np.array([pred]))[0][0]
    prediction = model.predict(x_next)[0]
    return prediction

class Worker():
    def __init__(self):
        self.items = []
        self.target = []
        self.index = []
        self.n = ceil(timeSeriesModel(_A)/e) # Automatic Sampling

    def insertItems(self, A, B, index):
        self.index.append(index)
        self.items.append([A,B])
        target = sample(self.n, A, B)
        self.target.append(target)

    def insertDriver(self, A, B):
        retVal = -1
        for i in range(len(self.items)):
            [C,D] = self.items[i]

            x = extraTime(A,B,C,D)
            print(x)
            if x < self.target[i]:
                retVal = i
                break

        if retVal == -1:
            return ''
        
        self.items.pop(retVal)
        self.target.pop(retVal)
        index = self.index.pop(retVal)

        return index 

if __name__ == '__main__':
    random.seed(180521)

    for i in range(0):
        C = randomCoord()
        D = randomCoord()
        print(extraTime(A,B,C,D))

    t = Worker()
    for i in range(3):
        A = randomCoord()
        B = randomCoord()
        t.insertItems(A,B, i)

    for j in range(10):
        A = randomCoord()
        B = randomCoord()
        val = t.insertDriver(A,B)
        if val != '':
            print(f'Completed pairing of rider {j} with route {val}')
