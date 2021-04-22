import ccxt
from functions import *
from pprint import pprint
import json
from tqdm import tqdm
import time
from progress.bar import Bar

def progressBar():
    bar = Bar('Processing', max=20)
    for i in range(20):
        time.sleep(0.1)
        bar.next()
    bar.finish()

def run():

    progressBar()

    return

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
