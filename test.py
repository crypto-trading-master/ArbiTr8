import ccxt
from functions import *
from pprint import pprint
import json


def run():

    exchange_class = getattr(ccxt, 'bittrex')
    exchange = exchange_class({
        'enableRateLimit': True
    })

    pair = 'BCH/BTC'
    markets = exchange.load_markets(True)

    tickers = exchange.fetch_tickers()


    # pprint(list(markets.keys()))
    pprint(tickers)




    # pprint(exchange.fetchOrderBook(pair))



    # order = exchange.create_market_sell_order('BNB/BTC', 0.03)


if __name__ == "__main__":
    run()
