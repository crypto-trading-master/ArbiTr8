import ccxt
from functions import *
from pprint import pprint
import json


def run():
    initialize()
    arbitrage()


def initialize():

    print("\n---------------------------------------------------------\n")
    print("Welcome to Triangular Arbitr8 Bot")
    print("\n---------------------------------------------------------\n")

    try:

        global baseCoins, coinBalance, exchange, exchanges, triplePairs, triples, \
               bestArbTriple, noOfTrades, minProfit, paperTrading, allPairs

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

        print("Number of base coins:", len(baseCoins), "\n")

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
        print(str(e))


def arbitrage():
    for tradeCounter in range(noOfTrades):
        getBestArbitrageTriple()


def getBestArbitrageTriple():

    print("\n\nCalculate current arbitrage possibilities...\n")

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

                            arbTriple['profit'] = profit
                            calcTriples.append(arbTriple)

                            if profit > maxProfit:
                                maxProfit = profit
                                bestArbTriple = arbTriple

    maxProfit = maxProfit - 1
    print(bestArbTriple['exchange'], \
          bestArbTriple['baseCoin'], \
          "max. Profit % ", \
          round(maxProfit * 100, 2), bestArbTriple['triple'])

    sortedArbTriples = sorted(calcTriples, key=lambda k: k['profit'], reverse=True)

    '''
    print("Number of calculated triples:", len(calcTriples))
    for triple in sortedArbTriples[:10]:
        profit = triple['profit'] - 1
        print(triple['exchange'], \
              triple['baseCoin'], \
              "max. Profit % ", \
              round((profit) * 100, 2), triple['triple'])
    '''

    verifyTripleDepthProfit(sortedArbTriples)

    return

    '''
        if maxProfit < minProfit:
            getBestArbitrageTriple()
        else:
            tradeArbTriple(bestArbTriple)

        # ############## TODO: Verify triple multiple times
    '''


def verifyTripleDepthProfit(arbTriples):

    for arbTriple in arbTriples[:1]:
        i = 0

        exchangeName = arbTriple['exchange']
        exchange[exchangeName].load_markets(True)

        triple = arbTriple['triple']
        coinAmountToTrade = arbTriple['coinAmountToTrade']

        print("Base coin:", arbTriple['baseCoin'], "\n")
        print()

        for pair in triple:

            i += 1

            orderBookLevel = 0
            totalQuantity = 0
            totalAmount = 0
            orderBookDepth = 0
            coinAmountTraded = 0

            print("Pair:", pair)
            print("Trade Action:", arbTriple[pair]['tradeAction'])
            print("Quantity to trade:", coinAmountToTrade)
            print()

            orderbook = exchange[exchangeName].fetch_order_book(pair)

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
                print("Level:", orderBookLevel)
                print("Quantity:", quantity)
                print("Price:", price)
                print("Amount:", amount)
                print("Total quantity", totalQuantity)
                print("Total amount:", totalAmount)
                print("Coin amount to trade:", coinAmountToTrade)
                print("Coin amount traded:", coinAmountTraded)
                print()

            coinAmountToTrade = coinAmountTraded

            if i == 3:
                profit = coinAmountTraded / arbTriple['coinAmountToTrade'] - 1
                print("Profit % after order book validation:", round(profit * 100, 2))



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


if __name__ == "__main__":
    run()
