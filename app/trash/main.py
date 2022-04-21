#!/usr/bin/python3
import requests
import uvicorn
import config
import sqlite3
import math
from datetime import datetime

#FastApi
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Text, Optional

#Binance
import ccxt

#Secrets
bot_token   = config.bot_token
bot_chatid  = config.bot_chatid
api_key     = config.api_key
api_sec     = config.api_sec

#Sets
binance     = ccxt.binance({'apiKey':api_key,'secret':api_sec,'timeout':30000,'enableRateLimit': True,
                            'options':{'defaultType':'future','warnOnFetchOpenOrdersWithoutSymbol':False}})
binance.load_markets()
app         = FastAPI()
con         = sqlite3.connect('tradinglog.db')

unit_usdt:float     = 5   #each trade in USDT
sl_factor:float     = 0.99 #security SL
tp_factor:float     = 1.02 #security TP
leverage:int        = 1    #default leverage


#Classes
class WhModel(BaseModel):
    strategy: str
    token: str
    close: float
    action: str
    direction: str
    interval: Optional[str]
    qtymultiplier: Optional[float]
    created_at: datetime = datetime.now()
    sent_at: Optional[str]
    comment: Optional[Text]
    volume: Optional[float]
    ohlc: Optional[list] = [0.0,0.0,0.0,0.0]


#Functions
def truncate(n, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * n) / stepper

def convert_symbol(symbol:str) -> str:
    "From BNBUSDT to BNB/USDT, or ETHBTC to ETH/BTC"
    l = 4 if symbol[-4:] in ['BUSD','USDT'] else 3
    stable = symbol[-l:]
    token  = symbol[:-l]
    return token + '/' + stable

def create_order(wh, leverage:int = 1):
    binance.fapiPrivate_post_leverage({'symbol':wh.token,'leverage':leverage})
    precision = int(binance.market(wh.token)['precision']['base'])
    
    ep:str  = "{:0.3f}".format(wh.close)
    sl:str  = "{:0.3f}".format(wh.close * sl_factor)
    tp:str  = "{:0.3f}".format(wh.close * tp_factor)
    qty = truncate(unit_usdt / wh.close, precision)
 
    telegram({'Info':'Placing order:',
              'EP': ep,
              'SL': sl,
              'TP': tp,
              'Qty': qty,
              'precision':precision})
    
    binance.create_market_buy_order(convert_symbol(wh.token), qty)
    binance.create_order()

    telegram({'Info','ORDERS SENT'})


def telegram(whdict:dict):
    s:str = ""
    for k, v in whdict.items():
        s = s + str(k) + ": " + str(v) + "\n"
    send_text = 'https://api.telegram.org/bot' + bot_token + \
                '/sendMessage?chat_id=' + bot_chatid + \
                '&parse_mode=html&text=' + s
    response = requests.get(send_text)


#Routes
@app.get('/')
def index() -> dict:
    return {'ping': 'pong! it´s working'}


@app.post('/wh')
def webhook(wh:WhModel):
    print(wh)
    telegram(wh.dict())
    create_order(wh)



if __name__ == '__main__':
    telegram({'Info':'Application initialized'})
    uvicorn.run('main:app', host='0.0.0.0', port=8080)
