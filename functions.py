from pprint import pprint
import logging
import time
import csv


def currentTimeStr():
    return time.strftime("%Y%m%d-%H%M%S")


def initCSV():
    global csvWriter

    filename = currentTimeStr() + ".csv"
    csvFile = open(filename, mode='w')
    csvWriter = csv.writer(csvFile, delimiter=';')
    csvWriter.writerow(["Exchange", "Triple", "Ticker profit %", "Order book profit %"])


def writeCSV(*texts):
    row = []
    row.append(currentTimeStr)
    row.extend(texts)
    csvWriter.writerow(row)


def initLogger():
    global logger

    timestr = time.strftime("%Y%m%d-%H%M%S")

    logging.basicConfig(filename=timestr + ".log", format='%(asctime)s %(message)s', filemode='w')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)


def printLog(*texts):
    outText = ' '.join(str(text) for text in texts)
    logger.info(outText)
    print(outText)


def isSpotPair(value):
    return True
    # return value['type'] == 'spot'


def isActiveMarket(value):
    return value['active'] is True


def isExchangeBaseCoinPair(baseCoin, pair):
    coins = getPairCoins(pair)
    for coin in coins:
        if coin == baseCoin:
            return True


def addTriplePair(triplePairs, pair):
    if pair not in triplePairs:
        triplePairs.append(pair)


def getPairCoins(pair):
    coins = pair.split("/")
    return coins


def coinIsPairBaseCoin(coinToCheck, pair):
    coins = getPairCoins(pair)
    return coinToCheck == coins[0]


def getOtherPairCoin(oneCoin, pair):
    coins = getPairCoins(pair)
    for coin in coins:
        if coin != oneCoin:
            return coin


def pairIsInTickers(pair, tickers):
    return pair in list(tickers.keys())


def tickerHasPrice(ticker):
    if ticker['ask'] is None or ticker['bid'] is None:
        return False
    return float(ticker['ask']) > 0 and float(ticker['bid']) > 0


def getBuyPrice(ticker):
    mode = 'ask'
    return ticker[mode]  # ask -> Get left pair coins


def getSellPrice(ticker):
    mode = 'bid'
    return ticker[mode]  # bid -> Get right pair coins
