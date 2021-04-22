import ccxt
from functions import *
from pprint import pprint
import json
import datetime
import time

def run():

    exchange_class = getattr(ccxt, 'binance')
    exchange = exchange_class({
        'enableRateLimit': True
    })

    exchange.load_markets(True)

    triple = ['MONA/BTC', 'MONA/USDT', 'BTC/USDT']

    pair = 'BTC/USDT'




    trades = exchange.fetch_trades(pair, limit=100)

    print("Number of Trades:", len(trades))
    pprint(trades)

    return

    orderbook = exchange.fetch_order_book(pair)

    # print("Orderbook depth:",len(orderbook['bids']))

    bidCumTotal = 0

    for i in range(0,4):
        bidPrice = orderbook['bids'][i][0]
        bidAmount = orderbook['bids'][i][1]
        bidTotal = bidPrice * bidAmount
        bidCumTotal += bidTotal
        print("Bid Price:", bidPrice)
        print("Bid Amount:", bidAmount)
        print("Bid Total:", bidTotal)
        print("Bid Volume:", bidCumTotal)
    #pprint(orderbook)

'''
Price (Quote Coin)
Amount (Base Coin)

= Total (Quote Coin)
'''


if __name__ == "__main__":
    run()
