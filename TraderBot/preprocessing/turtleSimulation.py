# import libraries
from utils import *
import os
import sys
import numpy as np
import pandas as pd
foldername = ['11_3-11_6/', '11_15-11_20/', '11_23-11_27/', '12_7-12_11/', '12_12-12_20/']
# portfolio = {"BTC":0.367972048,"ETH":0.237290852,"XRP":0.226306547,"LTC":0.168430552}


def main(argv):
    global foldername
    # Error checking
    if len(argv) is not 3:
        print("\nError: User must input 3 arguments:")
        print("\tArg1: ticks [str]")
        print("\tArg2: tick distribution [float]  0 < # > 1]")
        print("\tArg3: initial investmet [int]")
        print("NOTE: multi-variable arguments need to be comma delimited\n")
        return
    # unpack user input
    ticker, pdist, invest = argv
    ticker = ticker.split(',')
    pdist = list(map(float, pdist.split(',')))
    invest = int(invest)

    # initialize variables to track investment
    portfolio = dict(zip(ticker, pdist))

    perm_pchange = dict()
    for tick in ticker:
        perm_pchange[tick] = []

    dprofit = 0
    iprice = []
    fprice = []
    allChange = pd.DataFrame()
    # Cycle through obtained data
    for i, fn in enumerate(foldername):
        # initialize in-scope variables to track data specific gains
        discreteCryptoSeries = loadProcessedCryptoData(ticker, fn)
        pgain = dict()
        pmarg = dict()
        transcost = dict()
        totalprofits = 0
        totaltranscosts = 0
        sAmount = 0
        nSells = 0
        nSellsVal = 0

        invest = invest + dprofit
        print("#####################################################")
        print("Start of period %s Investment: \t%d" % (fn, invest))
        print("#####################################################")
        # Cycle through ticks
        for tick in ticker:
            allChange = pd.concat([allChange, discreteCryptoSeries[tick].V.dropna()])
            ts = discreteCryptoSeries[tick].LASTUPDATE
            if fn == foldername[0]:
                iprice.append(discreteCryptoSeries[tick].PRICE.values[0])
            if fn == foldername[-1]:
                fprice.append(discreteCryptoSeries[tick].PRICE.values[-1])
            print("%s investment: \t%f" % (tick, portfolio[tick] * invest))
            conf = np.max(discreteCryptoSeries[tick].MACD) * 0.1
            # Turtle Trading Full simulation
            pmarg[tick], pgain[tick], sAmount, bsDF, temp_pchange = turtletrading(discreteCryptoSeries[tick], conf=conf, amount=portfolio[tick] * invest, moff=True)
            perm_pchange[tick].extend(temp_pchange)
            nSells += np.sum(bsDF.Sell)
            nSellsVal += np.sum(sAmount)
            #     transaction costs --> 0.25%
            transcost[tick] = np.sum(sAmount * 0.0025)
            # calculate totals
            totalprofits += pgain[tick]
            totaltranscosts += transcost[tick]
            print("Marginal on Sales ", temp_pchange)
            print("Unit Profits:%f" % (pgain[tick]))
            print("Transaction Costs:%f\n\n" % (transcost[tick]))
            dprofit = totalprofits - totaltranscosts
        totalTime = ts[len(ts) - 1] - ts[0]
        print("Total profits: %d in %d second timeframe" % (totalprofits, totalTime))
        print("Total transaction costs: %d" % (totaltranscosts))
        print("Total Sells (#): %d Total Sells (VAL): %d" % (nSells, nSellsVal))
        print("Profit/Loss: %f" % (totalprofits - totaltranscosts))
    print("#####################################################")
    print("End investment", invest)
    print("#####################################################")
    return


if __name__ == "__main__":
    main(sys.argv[1:])
