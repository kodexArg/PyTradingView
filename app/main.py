#!/usr/bin/python3
import requests
import uvicorn
import sqlite3
from datetime import datetime

#This
import config
from kfunctions import * #part of this project

#FastApi
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Text, Optional

#Binance
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException



#Secrets
bot_token   = config.bot_token
bot_chatid  = config.bot_chatid
api_key     = config.api_key
api_sec     = config.api_sec

#Sets
debug       = False
binance     = Client(api_key, api_sec)
app         = FastAPI()
con         = sqlite3.connect('tradinglog.db')

unit_usdt:float     = 100   #max of trade unit in USDT.
sl_factor:float     = 0.05 #security SL when creating new orders, default 5%
tp_factor:float     = 0.1  #security TP when creating new orders, default 10%
leverage:int        = 3   #default leverage



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
def telegram(andydict:dict):
    s:str = ""
    for k, v in andydict.items():
        s = s + str(k) + ": " + str(v) + "\n"
    send_text = 'https://api.telegram.org/bot' + bot_token + \
                '/sendMessage?chat_id=' + bot_chatid + \
                '&parse_mode=html&text=' + s
    response = requests.get(send_text)


def close_cancel_orders(wh):
    if not is_open_position(wh.token, binance): #checks: non-existent position or no orders
        telegram({'<b>'+wh.token+'</b>':'error on cancel/close order',
                  'Err':'non-existent position. Nothing to do'})
        return None

    try:
        qty = get_order_qty(wh.token, binance)
        binance.futures_create_order(
            symbol          = wh.token,
            type            = 'MARKET',
            side            = SIDE_BUY if wh.action=='buy' else SIDE_SELL,
            quantity        = qty)

    except BinanceAPIException as e:
        telegram({'<b>'+wh.token+'</b>':'error on cancel/close order',
                  'Err':'<b>UNABLE TO CLOSE POSITION</b>. It must be closed manually',
                  e.status_code:e.message})

    else:
        binance.futures_cancel_all_open_orders(symbol=wh.token)
        this, last, profit = get_last_closed(wh.token, binance)
        telegram({'<b>'+wh.token+'</b>':'Closing all orders and trades.',
                 'Strategy':f'{wh.strategy} ({wh.action} qty {qty} @ {wh.close})',
                 'Profit':f'${profit:.2f} (wallet: {get_basepair_balance(wh.token, binance):.2f}'})


def create_new_orders(wh:dict, leverage:int = leverage):
    qty_precision     = int(get_quantity_precision(wh.token, binance))
    price_precision   = int(get_price_precision(wh.token, binance))
    qty = truncate((unit_usdt*leverage)/wh.close, qty_precision)

    if debug == True:
        telegram({
            'qty_precision':qty_precision,
            'price_precision':price_precision,
            'unit_usdt * leverage':unit_usdt*leverage,
            'price':wh.close,
            '<b>total</b>':((unit_usdt*leverage)/wh.close, qty_precision),
            'total truncated':qty
            })

    #some custom checks:
    if is_open_position(wh.token, binance):
        telegram({'<b>'+wh.token+'</b>':'error creating new order',
                  'Err': 'There is already an open position for this token. Sending close/cancel command...'})
        close_cancel_orders(wh)

    if float(qty) == 0:
        telegram({'<b>'+wh.token+'</b>':'error creating new order',
                  'Err':'Rounded quantity less than zero. Precision ='+str(qty_precision),
                  'Info':'Trade unit in usdt (currently $' + str(unit_usdt) +') is too small for this token.'})
        return None

    if is_open_order(wh.token, binance):
        telegram({'<b>'+wh.token+'</b>':'error creating new order',
                  'Err':'Open orders found for this token. This bot can´t set '+
                  'a safe Stop Loss and Take Profit order, this operation cannot continue. Nothing has been done'})
        return None

    binance.futures_change_leverage(symbol=wh.token, leverage=leverage)
    #binance.futures_change_margin_type(symbol=wh.token, marginType='ISOLATED') #fix pending: change to isolated if != isolated.


    sign    = 1 if wh.direction == 'long' else -1
    ep:str  = "{:0.{}f}".format(wh.close, price_precision)
    sl:str  = "{:0.{}f}".format(wh.close * (1 - sl_factor * sign),price_precision)
    tp:str  = "{:0.{}f}".format(wh.close * (1 + tp_factor * sign),price_precision)

    try:
        binance.futures_create_order(
            symbol    = wh.token,
            type      = 'MARKET',
            side      = SIDE_BUY if wh.action=='buy' else SIDE_SELL,
            quantity  = qty)

    except BinanceAPIException as e:
        telegram({'<b>'+wh.token+'</b>':'error creating new order',
                  e.status_code:e.message})

    else:
        binance.futures_create_order(
            symbol    = wh.token,
            type      = 'STOP_MARKET',
            side      = SIDE_BUY if wh.action=='sell' else SIDE_SELL,
            quantity  = qty,
            stopPrice = sl)

        binance.futures_create_order(
            symbol    = wh.token,
            type      = 'TAKE_PROFIT_MARKET',
            side      = SIDE_BUY if wh.action=='sell' else SIDE_SELL,
            quantity  = qty,
            stopPrice = tp)

        telegram({'Info':'Positioning <b>'+wh.token+'</b>',
                'Strategy':wh.strategy,
                'Action': wh.action+' '+wh.direction,
                'EP': ep,
                'SL': sl,
                'TP': tp,
                'Qty': qty,
                'Total Size:': f'<b>${qty*wh.close:.2f}</b> / {get_basepair_balance(wh.token, binance):.2f}'})


#Routes
@app.get('/')
def index() -> dict:
    return {'ping': 'pong! it´s working'}


@app.post('/wh')
def webhook(wh:WhModel):
    print('·' * 100)
    print(wh)
    print('·' * 100)
    #patching for xxxxxPERP tokens
    if wh.token[-4:] == 'PERP':
        if debug == True:
            telegram({'Info':f'fixing {wh.token} -> {wh.token[:-4]}'})
        wh.token = wh.token[:-4]
    if debug==True:
        telegram(wh.dict())
    if wh.direction != 'flat':
        create_new_orders(wh)
    elif wh.direction == 'flat':
        close_cancel_orders(wh)



#Run
if __name__ == '__main__':
    telegram({'Info':'Application initialized'})
    print('-' * 100)
    print('Reminder: make a route from port 80 to local 8080')
    print('-' * 100)
    uvicorn.run('main:app', host='0.0.0.0', port=8080)
