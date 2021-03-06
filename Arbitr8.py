import ccxt
from functions import *
from pprint import pprint
import json



def run():
    initialize()
    arbitrage()


def initialize():

    global baseCoins, coinBalance, exchange, exchanges, triplePairs, triples, \
           bestArbTriple, noOfTrades, minProfit, paperTrading, allPairs

    initCSV()
    initLogger()

    printLog("---------------------------------------------------------")
    printLog("Welcome to Triangular Arbitr8 Bot")
    printLog("---------------------------------------------------------")

    try:

        baseCoins = {}
        basePairs = {}
        allPairs = {}
        triplePairs = {}
        coinBalance = {}
        triples = {}
        exchange = {}

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

        printLog("Number of base coins:", len(baseCoins))
        print()
        printLog("Generating Triples...")
        print()

        exchanges = config['exchanges']

        for exchangeName in exchanges:

            print("Exchange:", exchangeName)

            allPairs[exchangeName] = []
            basePairs[exchangeName] = {}
            triplePairs[exchangeName] = {}
            triples[exchangeName] = {}

            exchange_class = getattr(ccxt, exchangeName)
            exchange[exchangeName] = exchange_class({
                'enableRateLimit': True,
                'apiKey': apiKey,
                'secret': secret
            })

            # TODO Secrets for every exchange -> Only needed when trading on exchange

            if config['useTestNet'] is True:
                exchange[exchangeName].set_sandbox_mode(True)

            markets = exchange[exchangeName].load_markets(True)

            for pair, value in markets.items():
                if isActiveMarket(value) and isSpotPair(value):
                    allPairs[exchangeName].append(pair)

            for baseCoin, baseCoinConfig in baseCoins.items():

                # Find Trading Pairs for base coin

                basePairs[exchangeName][baseCoin] = []
                coinsBetween = []

                for pair in allPairs[exchangeName]:
                    if isExchangeBaseCoinPair(baseCoin, pair):

                        # ######### TODO: Check market volume

                        basePairs[exchangeName][baseCoin].append(pair)

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

    except ccxt.ExchangeError as e:
        printLog(str(e))


def arbitrage():
    for tradeCounter in range(noOfTrades):
        getBestArbitrageTriple()


def getBestArbitrageTriple():

    print()
    printLog("Calculate current arbitrage possibilities...")
    print()

    global maxProfit
    maxProfit = 0
    bestArbTriple = {}
    calcTriples = []

    for exchangeName in exchanges:  # Loop exchanges

        print("Calculate", exchangeName)

        exchange[exchangeName].load_markets(True)
        tickers = exchange[exchangeName].fetch_tickers(allPairs[exchangeName])

        for baseCoin, baseCoinConfig in baseCoins.items():  # Loop Basecoins

            if len(triples[exchangeName][baseCoin]) > 0:

                coinBalance[baseCoin] = baseCoinConfig['startBalance']

                for triple in triples[exchangeName][baseCoin]:
                    i = 0
                    coinAmount = 0
                    transferCoin = ''
                    profit = 0
                    arbTriple = {}

                    arbTriple['triple'] = triple
                    arbTriple['exchange'] = exchangeName
                    arbTriple['baseCoin'] = baseCoin
                    arbTriple['coinAmountToTrade'] = coinBalance[baseCoin]

                    for pair in triple:
                        i += 1

                        if not pairIsInTickers(pair, tickers):
                            break

                        ticker = tickers[pair]

                        if not tickerHasPrice(ticker):
                            break

                        arbTriple[pair] = {}
                        arbTriple[pair]['pair'] = pair

                        if i == 1:
                            transferCoin = baseCoin
                            coinAmount = coinBalance[baseCoin]

                        if coinIsPairBaseCoin(transferCoin, pair):
                            arbTriple[pair]['baseCoin'] = transferCoin
                            arbTriple[pair]['quoteCoin'] = getOtherPairCoin(transferCoin, pair)
                            # Sell
                            tickerPrice = getSellPrice(ticker)
                            coinAmount = tickerPrice * coinAmount
                            arbTriple[pair]['tradeAction'] = 'sell'
                            arbTriple[pair]['tradePrice'] = 'bid'
                        else:
                            arbTriple[pair]['baseCoin'] = getOtherPairCoin(transferCoin, pair)
                            arbTriple[pair]['quoteCoin'] = transferCoin
                            # Buy
                            tickerPrice = getBuyPrice(ticker)
                            coinAmount = coinAmount / tickerPrice
                            arbTriple[pair]['tradeAction'] = 'buy'
                            arbTriple[pair]['tradePrice'] = 'ask'

                        arbTriple[pair]['calcPrice'] = tickerPrice
                        arbTriple[pair]['calcAmount'] = coinAmount
                        transferCoin = getOtherPairCoin(transferCoin, pair)
                        arbTriple[pair]['transferCoin'] = transferCoin

                        if i == 3:
                            profit = arbTriple[pair]['calcAmount'] / coinBalance[baseCoin]

                            arbTriple['tickerProfit'] = profit
                            if profit - 1 >= minProfit:
                                calcTriples.append(arbTriple)

                            if profit > maxProfit:
                                maxProfit = profit
                                bestArbTriple = arbTriple

    maxProfit = maxProfit - 1
    print()
    printLog("Number of potential triples:", len(calcTriples))
    printLog(bestArbTriple['exchange'], \
          bestArbTriple['baseCoin'], \
          "max. Profit % ", \
          round(maxProfit * 100, 2), bestArbTriple['triple'])
    print()

    sortedArbTriples = sorted(calcTriples, key=lambda k: k['tickerProfit'], reverse=True)

    verifyTripleDepthProfit(sortedArbTriples)


def verifyTripleDepthProfit(arbTriples):

    for arbTriple in arbTriples:
        i = 0
        tripleValid = True

        exchangeName = arbTriple['exchange']
        exchange[exchangeName].load_markets(True)

        triple = arbTriple['triple']
        coinAmountToTrade = arbTriple['coinAmountToTrade']

        for pair in triple:
            if tripleValid:

                i += 1

                orderBookLevel = 0
                totalQuantity = 0
                totalAmount = 0
                orderBookDepth = 0
                coinAmountTraded = 0

                orderbook = exchange[exchangeName].fetch_order_book(pair)

                if not (orderbook['asks'] or orderbook['bids']):
                    tripleValid = False
                    continue

                if arbTriple[pair]['tradeAction'] == 'sell':
                    orderBookAction = 'bids'
                else:
                    orderBookAction = 'asks'

                while coinAmountToTrade > 0:
                    price = orderbook[orderBookAction][orderBookLevel][0]  # Pair base coin
                    quantity = orderbook[orderBookAction][orderBookLevel][1]  # Pair quote coin
                    amount = price * quantity
                    totalQuantity += quantity
                    totalAmount += amount

                    if orderBookAction == 'bids':  # sell
                        # Check against order book quantity
                        orderBookDepth = totalQuantity
                        if coinAmountToTrade > orderBookDepth:
                            coinAmountTraded += orderBookDepth * price
                            coinAmountToTrade -= orderBookDepth
                        else:
                            coinAmountTraded += coinAmountToTrade * price
                            coinAmountToTrade = 0
                    else:  # buy
                        # Check against order book amount
                        orderBookDepth = totalAmount
                        if coinAmountToTrade > orderBookDepth:
                            coinAmountTraded += orderBookDepth / price
                            coinAmountToTrade -= orderBookDepth
                        else:
                            coinAmountTraded += coinAmountToTrade / price
                            coinAmountToTrade = 0

                    orderBookLevel += 1

                coinAmountToTrade = coinAmountTraded

                if i == 3:
                    profit = coinAmountTraded / arbTriple['coinAmountToTrade'] - 1

                    if profit >= minProfit:
                        tickerProfit = round((arbTriple['tickerProfit'] - 1) * 100, 2)
                        orderBookProfit = round(profit * 100, 2)
                        printLog("Exchange:", exchangeName)
                        printLog("Triple:", triple)
                        printLog("Ticker profit:", tickerProfit, "%")
                        printLog("Order book profit:", orderBookProfit, "%")
                        print()
                        writeCSV(exchangeName, triple, tickerProfit, orderBookProfit)
                    else:
                        getBestArbitrageTriple()  # Calc again


def tradeArbTriple(arbTriple):

    global coinBalance
    tradeAmount = coinBalance

    exchange.fetch_tickers()

    print("Start balance:", tradeAmount)

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


if __name__ == "__main__":
    run()
