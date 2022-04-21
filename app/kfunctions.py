import math

def get_last_closed(token, binance):
    this, last = {}, {}
    for order in binance.futures_get_all_orders(symbol=token)[-10:]:
        if order['status'] == 'FILLED':
            profit = float(order['avgPrice'])+float(order['origQty'])
            this, last = last, order
    if this['side'] != last['side']:
        result = (float(this['avgPrice']) * float(this['origQty']) - float(last['avgPrice']) * float(last['origQty']))
    else:
        result = None
    return this, last, result


def get_balance(binance) -> list:
    balance = []
    for acc_balance in binance.futures_account_balance():
        if float(acc_balance['balance']) != 0:
            balance.append("{}: {:.2f}".format(acc_balance['asset'], float(acc_balance['balance'])))
    return balance


def get_basepair_balance(symbol, binance) -> float:
    #indetify asset
    for o in binance.futures_account_balance():
        coin = o['asset']
        if symbol[-len(coin):] == coin:
            return float(o['balance'])
    return 0.0

def truncate(n, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * n) / stepper


def is_open_position(symbol, binance) -> bool:
    for p in binance.futures_position_information():
        if float(p['positionAmt']) != 0:
            if p['symbol'] == symbol:
                return True
    return False


def is_open_order(symbol, binance) -> bool:
    return True if symbol in binance.futures_get_open_orders() else False


def get_quantity_precision(symbol, binance) -> int:
    info = binance.futures_exchange_info()
    info = info['symbols']
    for x in range(len(info)):
        if info[x]['symbol'] == symbol:
            return int(info[x]['quantityPrecision'])
    return 0


def get_price_precision(symbol, binance) -> int:
    info = binance.futures_exchange_info()
    info = info['symbols']
    for x in range(len(info)):
        if info[x]['symbol'] == symbol:
            return int(info[x]['pricePrecision'])
    return 0


# def get_order_qty(symbol, binance) -> float:
#     for order in binance.futures_get_open_orders():
#         if order['symbol']==symbol:
#             return float(order['origQty'])
#     return 0

def get_order_qty(symbol, binance) -> float:
    pos = binance.futures_position_information(symbol=symbol)
    return abs(float(pos[0]['positionAmt']))
