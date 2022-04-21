def get_quantity_precision(symbol):    
    info = binance.futures_exchange_info() 
    info = info['symbols']
    for x in range(len(info)):
        if info[x]['symbol'] == symbol:
            return info[x]['pricePrecision']
    return None

    precision = int(get_quantity_precision(wh.token))
     binance.futures_change_leverage(symbol=wh.token, leverage=leverage) 


         if True:
        order_entry = binance.futures_create_order(
                symbol    = wh.token,
                type      = 'MARKET',
                side      = 'BUY',
                quantity  = qty)
        order_stop = binance.futures_create_order(
                symbol    = wh.token,
                type      = 'STOP_MARKET',
                side      = 'SELL',
                stopPrice = sl)
        order_prof = binance.futures_create_order(
                symbol    = wh.token,
                type      = 'TAKE_PROFIT_MARKET',
                side      = 'SELL',
                stopPrice = tp)



                    if symbol[-4:] in ['BUSD','USDT']:
        base = symbol[-4:]
        token = symbol[:-4]
    elif symbol[-3:] in ['BNB','ETH','BTC']:       
        base = symbol[-3:]
        token = symbol[:-3]
    else:
