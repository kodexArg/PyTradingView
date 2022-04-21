#!/usr/bin/python3
import datetime
import pandas as pd
import pandas_ta

#Binance
from binance.client import Client
from binance.enums import *

#Secrets
import config
api_key     = config.api_key
api_sec     = config.api_sec

#Sets
binance     = Client(api_key, api_sec)
SYMBOL      = "BNBUSDT"
INTERVAL    = "1m"

#Logic
def get_klines(hours:int=24) -> pd.DataFrame():
    now = datetime.datetime.now()
    past = now - datetime.timedelta(hours=hours)
    df = pd.DataFrame(
        binance.futures_historical_klines(
            symbol=SYMBOL,
            interval=INTERVAL,
            start_str=past.strftime("%Y-%m-%d"),
            end_str=now.strftime("%Y-%m-%d"),
        )
    )
    return df

df = get_klines(5)
print(df.ta.atr())