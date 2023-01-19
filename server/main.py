from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import math
import pandas_datareader as web
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
import datetime

app = FastAPI()
origins = [
    'http://localhost:3000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

@app.get("/fx")
def fx_data(from_,to_):
    # url = 'https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=EUR&to_symbol=USD&apikey=demo'
    url = f'https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_}&to_symbol={to_}&apikey=4THZE2SRL8MOGD1C'
    r = requests.get(url)
    data = json.loads(r.text)
    data = data['Time Series FX (Daily)']
    print(data)
    fx_data = []

    for i,df in enumerate(data):
        column = []
        fx = data
        column.append(df) #日時
        column.append(float(fx[df]['1. open']))#始値
        column.append(float(fx[df]['2. high'])) #高値
        column.append(float(fx[df]['3. low'])) #安値
        column.append(float(fx[df]['4. close'])) #終値
        fx_data.append(column)

    fx_df = pd.DataFrame(fx_data)
    fx_df = fx_df.set_axis(['Datetime', 'open', 'high', 'low', 'close'], axis=1)

    #dfから終値だけのデータフレームを作成する。（インデックスは残っている）
    rdata = fx_df.filter(['close']) 
    #dataをデータフレームから配列に変換する。
    dataset = rdata.values

    #トレーニングデータを格納するための変数を作る。
    #データの80%をトレーニングデータとして使用する。
    #math.ceil()は小数点以下の切り上げ
    training_data_len = math.ceil(len(dataset) * .8)

    #データセットを0から1までの値にスケーリングする。
    scaler = MinMaxScaler(feature_range=(0, 1)) 
    #fitは変換式を計算する
    #transform は fit の結果を使って、実際にデータを変換する
    scaled_data = scaler.fit_transform(dataset)

    train_data = scaled_data[0:training_data_len, :]

    #データをx_trainとy_trainのセットに分ける
    x_train = []
    y_train = []
    for i in range(60, len(train_data)):
        x_train.append(train_data[i-60:i, 0])
        y_train.append(train_data[i, 0])


    x_train, y_train = np.array(x_train), np.array(y_train)

    #LSTMに受け入れられる形にデータをつくりかえます
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    #LSTMモデルを構築して、50ニューロンの2つのLSTMレイヤーと2つの高密度レイヤーを作成します。（1つは25ニューロン、もう1つは1ニューロン）
    #Build the LSTM network model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True,input_shape=(x_train.shape[1],1)))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dense(units=25))
    model.add(Dense(units=1))

    #平均二乗誤差（MSE）損失関数とadamオプティマイザーを使用してモデルをコンパイルします。
    model.compile(optimizer='adam', loss='mean_squared_error')

    #Train the model
    model.fit(x_train, y_train, batch_size=1, epochs=1)

    #Test data set
    test_data = scaled_data[training_data_len - 60: , : ]

    #Create the x_test and y_test data sets
    x_test = [] #予測値をつくるために使用するデータを入れる
    y_test =  dataset[training_data_len : , : ] #実際の終値データ

    for i in range(60,len(test_data)):
        x_test.append(test_data[i-60:i,0]) #正規化されたデータ

    #Convert x_test to a numpy array 
    x_test = np.array(x_test)

    #Reshape the data into the shape accepted by the LSTM
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

    #Now get the predicted values from the model using the test data.
    #Getting the models predicted price values
    predictions = model.predict(x_test)
    predictions = scaler.inverse_transform(predictions) #Undo scaling

    #Calculate/Get the value of RMSE
    rmse = np.sqrt(np.mean(predictions - y_test) ** 2)

    rmse

    #Let’s plot and visualize the data.
    #Plot/Create the data for the graph
    train = rdata[:training_data_len]
    valid = rdata[training_data_len:]
    valid['Predictions'] = predictions#Visualize the data

 
    # data = df.to_json(valid)

    print(valid)
    return {
        "train":pd.DataFrame(train).to_json(),
        "valid":pd.DataFrame(valid).to_json()
    }