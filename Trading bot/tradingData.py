import pandas as pd
import sqlalchemy
from binance.client import Client
from binance import BinanceSocketManager, AsyncClient
import asyncio
import socket
import websockets
import json
import ta

api_key =''
api_secret = ''
stream = websockets.connect('wss://stream.binance.com:9443/stream?streams=btcusdt@miniTicker')





async def main():
    open_position = False
    df = pd.DataFrame()
    client = Client(api_key,api_secret)
    async with stream as receiver:
            while True:
                data = await receiver.recv()
                data = json.loads(data)['data']
                df = df.append(createframe(data))
                if len(df) > 30:
                    if not open_position:
                        if ta.momentum.roc(df.Price, 30).iloc[-1] > 0 and ta.momentum.roc(df.Price, 30).iloc[-2]:
                            order = client.create_order(symbol='BTCUSDT', side='BUY', type='MARKET', quantity=0.00041)

                            print(order)
                            open_position = True
                            buyprice = float(order['fills'][0]['price'])
                        
                    if open_position:
                        subdf = df[df.Time >= pd.to_datetime(order['transactTime'], unit='ms')]
                        if len(subdf) > 1:
                            subdf['highest'] = subdf.Price.cummax()
                            subdf['trailingstop'] = subdf['highest'] * 0.995
                            if subdf.iloc[-1].Price < subdf.iloc[-1].trailingstop or df.iloc[-1].Price / float(order['fills'][0]['price']) > 1.002:
                                order = client.create_order(symbol = 'BTCUSDT', side='SELL', type = 'MARKET', quantity=0.00041)
                                print(order)
                                sellprice = float(order['fills'][0]['price'])
                                print("You made" + {(sellprice - buyprice)/buyprice} + "profit")
                                open_position = False
                
                    print(df.iloc[-1])



def createframe(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:,['s','E', 'c']]
    df.columns = ['Symbol', 'Time', 'Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='ms')
    return df

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())




