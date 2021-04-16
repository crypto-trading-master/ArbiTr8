import ccxt
from functions import *
from pprint import pprint
import json


def run():
    initialize()
    # arbitrage()
    # test()


def initialize():

    print("\n---------------------------------------------------------\n")
    print("Welcome to Triangular Arbitr8 Bot")
    print("\n---------------------------------------------------------\n")

    try:

        global baseCoins, baseCoin, coinBalance, exchange, triplePairs, triples, \
               bestArbTriple, noOfTrades, minProfit, paperTrading

        baseCoins = {}
        basePairs = {}
        allPairs = {}
        triplePairs = {}
        coinBalance = {}
        triples = {}

        with open('config.json', 'r') as f:
            config = json.load(f)

        with open('secret.json', 'r') as f:
            secretFile = json.load(f)

        if config['useTestNet'] is True:
            apiKey = secretFile['testApiKey']
            secret = secretFile['testSecret']
        else:
            apiKey = secretFile['apiKey']
            secret = secretFile['secret']

        paperTrading = config['paperTrading']
        noOfTrades = config['noOfTrades']
        minProfit = config['minProfit']

        baseCoins = config['baseCoins']

        print("Number of base coins:", len(baseCoins))

        exchanges = config['exchanges']

        for exchangeName in exchanges:

            # TODO Progress Bar ############

            print("Exchange:", exchangeName)

            allPairs[exchangeName] = []
            basePairs[exchangeName] = {}
            triplePairs[exchangeName] = {}
            triples[exchangeName] = {}


            exchange_class = getattr(ccxt, exchangeName)
            exchange = exchange_class({
                'enableRateLimit': True,
                'apiKey': apiKey,
                'secret': secret
            })

            # TODO Secrets for every exchange -> Only needed when trading on exchange

            if config['useTestNet'] is True:
                exchange.set_sandbox_mode(True)
            markets = exchange.load_markets()

            for pair, value in markets.items():
                if isActiveMarket(value) and isSpotPair(value):
                    allPairs[exchangeName].append(pair)

            print("\nGenerating triples...\n")

            tickers = exchange.fetch_tickers(allPairs[exchangeName])
            for pair in allPairs[exchangeName]:
                if not tickerHasPrice(tickers[pair]):
                    allPairs[exchangeName].remove(pair)
            print("Number of valid market pairs:", len(allPairs[exchangeName]))

            for baseCoin, baseCoinConfig in baseCoins.items():

                # Find Trading Pairs for base coin

                basePairs[exchangeName][baseCoin] = []
                coinsBetween = []

                for pair in allPairs[exchangeName]:
                    if isExchangeBaseCoinPair(baseCoin, pair):

                        # ######### TODO: Check market volume

                        basePairs[exchangeName][baseCoin].append(pair)

                # print("Number of base coin pairs", baseCoin, len(basePairs[baseCoin]))

                # Find between trading pairs

                for pair in basePairs[exchangeName][baseCoin]:
                    coins = getPairCoins(pair)
                    for coin in coins:
                        if coin != baseCoin:
                            if coin not in coinsBetween:
                                coinsBetween.append(coin)

                # Check if between pair exists

                pairsBetween = []
                coinsBetween2 = coinsBetween

                for baseCoinBetween in coinsBetween:
                    for qouteCoinBetween in coinsBetween2:
                        pair = baseCoinBetween + "/" + qouteCoinBetween
                        if pair in allPairs[exchangeName]:
                            pairsBetween.append(pair)

                # Find triples for base coin

                triples[exchangeName][baseCoin] = []
                triplePairs[exchangeName][baseCoin] = []
                basePairs2 = basePairs[exchangeName][baseCoin]

                for pair in basePairs[exchangeName][baseCoin]:
                    firstCoins = getPairCoins(pair)
                    for firstCoin in firstCoins:
                        if firstCoin != baseCoin:
                            firstTransferCoin = firstCoin
                    for pairBetween in pairsBetween:
                        betweenPairFound = False
                        secondCoins = getPairCoins(pairBetween)
                        for secondCoin in secondCoins:
                            if secondCoin == firstTransferCoin:
                                betweenPairFound = True
                                secondPairCoin = secondCoin
                            else:
                                secondTransferCoin = secondCoin
                        if betweenPairFound:
                            for lastPair in basePairs2:
                                thirdCoins = getPairCoins(lastPair)
                                for thirdCoin in thirdCoins:
                                    if thirdCoin != baseCoin:
                                        thirdPairCoin = thirdCoin

                                if firstTransferCoin == secondPairCoin and \
                                   secondTransferCoin == thirdPairCoin:
                                    triple = []
                                    triple.append(pair)
                                    addTriplePair(triplePairs[exchangeName][baseCoin], pair)
                                    triple.append(pairBetween)
                                    addTriplePair(triplePairs[exchangeName][baseCoin], pairBetween)
                                    triple.append(lastPair)
                                    addTriplePair(triplePairs[exchangeName][baseCoin], lastPair)
                                    # Add triple to array of triples
                                    triples[exchangeName][baseCoin].append(triple)

                # print("Number of Triples:", len(triples[exchangeName][baseCoin]))
                # print("Number of Triple Pairs:", len(triplePairs[exchangeName][baseCoin]))

    except ccxt.ExchangeError as e:
        print(str(e))


##################################
#### TODO Continue here TODO #####
##################################

def arbitrage():
    for tradeCounter in range(noOfTrades):
        getBestArbitrageTriple()


def getBestArbitrageTriple():

    print("\n\nCalculate current arbitrage possibilities...\n")

    global maxProfit
    maxProfit = 0
    bestArbTriple = {}

    for baseCoin, baseCoinConfig in baseCoins.items():  # Loop Basecoins

        coinBalance[baseCoin] = baseCoinConfig['startBalance']

        exchange.load_markets(True)
        tickers = exchange.fetch_tickers(triplePairs[baseCoin])

        for triple in triples[baseCoin]:
            i = 0
            coinAmount = 0
            transferCoin = ''
            profit = 0
            arbTriple = {}

            arbTriple['triple'] = triple

            for pair in triple:
                i += 1
                ticker = tickers[pair]

                arbTriple[pair] = {}
                arbTriple[pair]['pair'] = pair

                if i == 1:
                    transferCoin = baseCoin
                    coinAmount = coinBalance[baseCoin]

                if coinIsPairBaseCoin(transferCoin, pair):
                    arbTriple[pair]['baseCoin'] = transferCoin
                    # ######### TODO arbTriple[pair]['quoteCoin']
                    # Sell
                    tickerPrice = getSellPrice(ticker)
                    coinAmount = tickerPrice * coinAmount
                    arbTriple[pair]['tradeAction'] = 'sell'
                else:
                    # ######### TODO arbTriple[pair]['baseCoin']
                    arbTriple[pair]['quoteCoin'] = transferCoin
                    # Buy
                    tickerPrice = getBuyPrice(ticker)
                    coinAmount = coinAmount / tickerPrice
                    arbTriple[pair]['tradeAction'] = 'buy'

                arbTriple[pair]['calcPrice'] = tickerPrice
                arbTriple[pair]['calcAmount'] = coinAmount
                transferCoin = getTransferCoin(transferCoin, pair)
                arbTriple[pair]['transferCoin'] = transferCoin

                if i == 3:
                    profit = arbTriple[pair]['calcAmount'] / coinBalance[baseCoin]
                    if profit > maxProfit:
                        maxProfit = profit
                        bestArbTriple['baseCoin'] = baseCoin
                        bestArbTriple['triple'] = triple

    maxProfit = maxProfit - 1
    print(bestArbTriple['baseCoin'], "max. Profit % ", round((maxProfit) * 100, 2), bestArbTriple['triple'])

    return

    '''
        if maxProfit < minProfit:
            getBestArbitrageTriple()
        else:
            tradeArbTriple(bestArbTriple)

        # ############## TODO: Verify triple multiple times
    '''


def tradeArbTriple(arbTriple):
    global coinBalance
    tradeAmount = coinBalance

    exchange.fetch_tickers()

    print("\nStart balance:", tradeAmount)

    for pair in arbTriple['triple']:
        side = arbTriple[pair]['tradeAction']

        print("Trading pair:", pair)
        print("Trade action:", side)
        print("Coin amount to trade:", tradeAmount)

        if paperTrading is True:
            exchange.load_markets(True)
            orderbook = (exchange.fetchOrderBook(pair))
            bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else 0
            ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else 0

            if side == 'buy':
                tradeAmount = tradeAmount / ask
            else:
                tradeAmount = tradeAmount * bid
        else:   # No Paper Trading
            if side == 'buy':
                params = {}
                amount = 0
                params['quoteOrderQty'] = exchange.costToPrecision(pair, tradeAmount)
                order = exchange.create_market_buy_order(pair, amount, params)
                # order = exchange.create_order(pair, type, side, amount, price, params)
            else:
                order = exchange.create_market_sell_order(pair, tradeAmount)

            tradeAmount = order['filled']

    print("End balance:", tradeAmount)
    coinBalance = tradeAmount

def test():

    pair = 'LTC/BNB'

    exchange.load_markets(True)
    tickers = exchange.fetch_tickers(pair)



    pprint(tickers[pair])




    pprint(exchange.fetchOrderBook(pair))



    # order = exchange.create_market_sell_order('BNB/BTC', 0.03)




if __name__ == "__main__":
    run()
