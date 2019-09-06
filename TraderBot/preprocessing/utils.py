import numpy as np
import pandas as pd
path = '/Users/maxmaguire/Desktop/PostGradWork/Projects/Data/HistoricalData/HFT_Data/'
# Helper functions


def feature_scale(data, scale=[-1, 1]):
    """
    feature scaling
    """
    data = np.ma.array(data, mask=np.isnan(data))
    dmax = np.amax(data)
    dmin = np.amin(data)
    # rescale
    output = (data - dmin) / (dmax - dmin) + scale[0] / 2
    return output * (scale[1] - scale[0])


def serialCorr(wave1, wave2, lag=1):
    """
    serial correlation
    """
    y1 = wave1
    y2 = np.roll(wave2, -lag)
    pcorr_mat = np.corrcoef(y1, y2)
    return pcorr_mat[0, 1]


def autoCorr(wave1, wave2):
    """
    autocorrelation
    """
    # disregard nan values
    wave1 = np.ma.array(wave1, mask=np.isnan(wave1))
    wave2 = np.ma.array(wave2, mask=np.isnan(wave2))

    n = len(wave1)
    autocorr_mat = np.zeros([n - 1, 1])

    index = np.arange(-n // 2 + 1, n // 2)
    for i, templag in enumerate(index):
        autocorr_mat[i, 0] = serialCorr(wave1, wave2, lag=templag)

    return pd.DataFrame(autocorr_mat[:, 0], index=index)


def turtletrading(discreteData, conf=0, amount=1000, moff=False):
    """
    DAMC turtle trading strategy implementation
    """
    pgain = dict()
    # compute long/short smoothed curve
    discreteData['MACD'].fillna(value=0, inplace=True)  # 0
    discreteData['Volatility'].fillna(value=0, inplace=True)  # 0

    volatility = feature_scale(discreteData.Volatility.values, scale=[0, 1])

    signalLine = discreteData.MACD.values
    prices = discreteData.PRICE
    t = discreteData.LASTUPDATE.values
    BSdata = pd.DataFrame({'LASTUPDATE': t,
                           'price': prices.values,
                           'Buy': [0] * len(signalLine),
                           'Sell': [0] * len(signalLine)})
    # plot macd
    dt = t - t[0]
    # Find point of rolling curve intersection
    BSdata.loc[signalLine < conf, 'Sell'] = 1
    BSdata.loc[signalLine > conf, 'Buy'] = 1

    BSdata['Buy'].values[1:] = np.diff(BSdata['Buy'].values)
    BSdata['Sell'].values[1:] = np.diff(BSdata['Sell'].values)

    BSdata.loc[BSdata['Buy'].values < 0, 'Buy'] = 0
    BSdata.loc[BSdata['Sell'].values < 0, 'Sell'] = 0

    firstBuyIDX = np.argmax(BSdata.Buy.values)
    firstSellIDX = np.argmax(BSdata.Sell.values)

    if firstSellIDX < firstBuyIDX:  # can't sell before you buy
        BSdata.Sell.values[firstSellIDX] = 0

    # Sell at end to cash out
    if np.sum(BSdata.Buy.values) > np.sum(BSdata.Sell.values) or np.sum(BSdata.Sell.values) < 1:
        BSdata.Sell.values[-1] = 1

    # print total number of buys and total number of sells
    struth = BSdata.Sell.values.astype(bool)
    btruth = BSdata.Buy.values.astype(bool)

    bprice = prices[btruth].values
    sprice = prices[struth].values

    # calculate profits from initial investment
    pchange = sprice / bprice
    # Determine buy/Sell multiplier based on volatility
    if moff:
        Bmultiplier = np.ones(len(bprice))
        Smultiplier = np.ones(len(sprice))
    else:
        Bmultiplier = Bmultiplier & volatility[btruth] > 0.2
        Smultiplier = Smultiplier & volatility[struth] > 0.2

    Smultiplier[-1] = 1

    iAmount = amount  # initial amount
    xAmount = 0       # investment in crypto-exchange
    profits = iAmount  # investment in USD
    moneyOut = np.zeros(len(pchange))
    moneyIn = np.zeros(len(pchange))

    for i in range(0, len(pchange)):
        if profits > 0:
            moneyIn[i] = profits * Bmultiplier[i]  # how much of investment to put in at time
            xAmount += moneyIn[i]
            profits -= moneyIn[i]
        moneyOut[i] = xAmount * Smultiplier[i]  # how much of investment to take out
        profits += moneyOut[i] * pchange[i]
        xAmount -= moneyOut[i]

    # calculate percentage gain
    pgain = np.sum(moneyOut * pchange) / np.sum(moneyIn) - 1
    return pgain, profits - iAmount, moneyOut, BSdata, pchange


def plotResults(ts, bsDF, tick, pmarg):
    """
    Plot results of Turtle trading strategy
    """
    dt = ts - ts[0]
    # show buy and sell timepoints
    btruth = bsDF.Buy.astype(bool)
    struth = bsDF.Sell.astype(bool)
    plt.plot(dt, bsDF.price.values, '0.7')
    plt.plot(dt[btruth], bsDF.price[btruth].values, 'bo')
    plt.plot(dt[struth], bsDF.price[struth].values, 'ro')
    plt.xlabel('time(s)')
    plt.title('MACD trading strategy %s\n%s Profit Margins: %3f' % (datetime.fromtimestamp(ts[0]), tick, pmarg * 100))
    plt.legend(['Price', 'Buy', 'Sell'])
    plt.show()
    return


def loadProcessedCryptoData(ticker, foldername, dataType='CRYPTO'):
    """
    load discretized data
    """
    global path
    cSeries = dict()
    if (dataType == 'Crypto' or dataType == 'Twitter' or dataType == 'GOOGLE'):
        return None
    for tick in ticker:
        fname = path + foldername + 'processedData/' + tick + 'discrete' + dataType + '.csv'
        cSeries[tick] = pd.read_csv(fname)
    return cSeries


def loadPostProcessedData(folderpath, tick, dropXLabel=None):
    # initialize vars
    global path
    filename = 'postprocessedData/'
    Xdata = dict()
    timing = list()
    # build filenames
    fnameX = path + folderpath + filename + tick + 'cryptoX_array.csv'
    fnameY = path + folderpath + filename + tick + 'cryptoY_array.csv'
    # load data
    Xarray = pd.read_csv(fnameX)
    Yarray = pd.read_csv(fnameY)
    # remove undesirable columns
    Xarray.drop('Unnamed: 0', axis=1, inplace=True)  # remove undesirable columns
    Yarray.drop('Unnamed: 0', axis=1, inplace=True)  # remove undesirable columns
    cdata = loadProcessedCryptoData([tick], folderpath, dataType='CRYPTO')  # load original price values
    timing.append(datetime.fromtimestamp(Xarray.LASTUPDATE[0]))  # retrieve ts of data start
    if dropXLabel:
        for lx in dropXLabel:
            Xarray.drop(lx, axis=1, inplace=True)
    Xarray = Xarray.dropna()
    Yarray = Yarray.dropna()
    pvalues = cdata[tick].RollingMeanShort.values[Xarray.index[0:]]
    timing.append(cdata[tick].LASTUPDATE[Xarray.index[0]])  # retrieve ts of model train
    # remove rows that don't contain data and re-index
    Xarray.index = range(0, len(Xarray.index))
    Yarray.index = range(0, len(Yarray.index))
    return Xarray, Yarray, pvalues, timing
