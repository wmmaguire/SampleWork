# imported libraries
import os
import sys
import numpy as np
import pandas as pd
import re
import math
import time
from datetime import datetime, timedelta
# global variables
regexp = re.compile('[^A-Z-]')
ticker = ['BTC', 'ETH', 'LTC', 'XRP']
keywords = ["bitcoin", "ethereum", "litecoin", "ripple"]

""" Retrieve all data files """


def retrieveFileasPD(path, ftype='CRYPTO', dtype=None, usecols=None):
    """
    Return data pertaining to ftype in path-->output [pd.DataFrame]
    """
    fnames = os.listdir(path)
    for f in fnames:
        if f[-4:] == '.csv' and ftype in f:
            return pd.read_csv(path + '/' + f, dtype=dtype, usecols=usecols)
    return None


def retrieveRawCryptoData(path):
    """
    retrieve raw crypto data in path --> output [pd.DataFrame]
    """
    # retrieve file as pandas Dataframe
    cryptoDataFULL = retrieveFileasPD(path, ftype='CRYPTO')
    # # remove undesirable columns and sort lastupdate values
    cryptoDataFULL = cryptoDataFULL.sort_values('LASTUPDATE')
    cryptoDataFULL.drop('Unnamed: 0', axis=1, inplace=True)
    return cryptoDataFULL


def retrieveRawTwitterData(path):
    """
    retrieve raw Twitter data in path --> output [pd.DataFrame]
    """
    # retrieve file as pandas Dataframe
    twitterDataFULL = retrieveFileasPD(path, ftype='Twitter',
        usecols=['compound', 'created_at', 'followers_count', 'friends_count', 'keyword',
       'negative', 'neutral', 'positive', 'statuses_count'])
    # make sure timeing in correct
    twitterDataFULL = twitterDataFULL[twitterDataFULL['created_at'] >= twitterDataFULL['created_at'].values[0]]
    # re-index
    twitterDataFULL.index = range(0, len(twitterDataFULL.index))
    return twitterDataFULL


def retrieveRawGoogleData(path):
    """
    retrieve raw Twitter data in path --> output [pd.DataFrame]
    """
    # retrieve file as pandas Dataframe
    googleDataFULL = retrieveFileasPD(path, ftype='Google')
    # remove  rows duplicates
    googleDataFULL = googleDataFULL.drop_duplicates(subset='date', keep='last')
    googleDataFULL['date'] = date_to_timestamp(googleDataFULL.date.values)  # reformatting time
    # re-index
    googleDataFULL.index = range(0, len(googleDataFULL.index))
    return googleDataFULL


def discretizeGoogleData(googleDataFULL, t):
    """
    Discretize Google data
    """
    # create discretization mask
    mask = np.arange(0, len(t))
    mask = list(np.full_like(mask, np.nan, dtype=np.double))
    # create a new discrete dataframe
    discretegoogleSeries = pd.DataFrame({'date': t,
                                'bitcoin': mask,
                                'ethereum': mask,
                                'litecoin': mask,
                                'ripple': mask})
    # create discrete time range
    timesteps = t.copy()
    timesteps.append(timesteps[-1] + 1)
    # create list of columns
    cols = [c for c in discretegoogleSeries.columns if c is not 'date']
    # bin data
    for ts_idx in range(1, len(timesteps)):
        # Match timestep indices
        truthpd  = (googleDataFULL.date.values >= timesteps[ts_idx-1]) & (googleDataFULL.date.values < timesteps[ts_idx])
        if truthpd.any():
            # Fill in matching indices (Fill the seconds before that aren't matched)
            for header in cols:
                discretegoogleSeries[header].values[ts_idx-1]   = np.mean(googleDataFULL[header].values[truthpd])

    # replace remaining nan values with prev real value
    for header in cols:
        discretegoogleSeries[header].fillna(method='ffill', inplace=True) # most recent val

    print("Google data spans %d timepoints"%(len(discretegoogleSeries.index)))
    return discretegoogleSeries

def discretizeTwitterData(twitterDataFULL,t):
    """
    discretize Twitter data
    """
    # create discretization mask
    mask     = np.arange(0,len(t))
    mask     = list(np.full_like(mask, np.nan, dtype=np.double))
    # HARDCODED keywords/ticker
    ticker = ["BTC","ETH","LTC","XRP"]
    keywords = ["bitcoin",
                "ethereum",
                "litecoin",
                "ripple"]
    # separate twitter data by keywords
    nullkeywords  = twitterDataFULL['keyword'].isnull()
    discretetwitterSeries = dict()
    # create timesteps
    timesteps = t.copy()
    timesteps.append(timesteps[-1]+1)
    for i,tick in enumerate(ticker): # Cycle through tick parameters
        # create a new discrete dataframe
        tickTwitterSeries = pd.DataFrame({'created_at': t,
                                 'friendsCompoundWeight' : mask,
                                 'followersCompoundWeight': mask,
                                 'statusesCompoundWeight': mask,
                                 'followersPositiveWeight': mask,
                                 'negative': mask,
                                 'positive': mask,
                                 'compound_score':mask,
                                 'number': mask })
        tickTwitterSeries.index = range(0,len(t))
        # store columns in new datafield
        cols = [c for c in tickTwitterSeries.columns if c is not 'created_at']
        # sort tweets into respective keyword fields
        ktruth = twitterDataFULL['keyword'].str.contains('|'.join([tick,keywords[i]]))
        ktruth.fillna(value=True, inplace=True)
        tick_df = twitterDataFULL[ktruth]
        tick_df.index = range(0,len(tick_df.index))
        # Create truth table that matches with discretized time frame
        tsTransformed = tick_df.created_at.values//1e3
        for ts_idx in range(1,len(timesteps)):
            # Match timestep indices
            truthpd  = (tsTransformed >= timesteps[ts_idx-1]) & (tsTransformed < timesteps[ts_idx])
            if truthpd.any():
                # fill in recorded values
                tickTwitterSeries.friendsCompoundWeight.values[ts_idx-1]   = np.dot(tick_df.friends_count.values[truthpd],tick_df['compound'].values[truthpd])
                tickTwitterSeries.followersCompoundWeight.values[ts_idx-1] = np.dot(tick_df.followers_count.values[truthpd],tick_df['compound'].values[truthpd])
                tickTwitterSeries.statusesCompoundWeight.values[ts_idx-1]  = np.dot(tick_df.statuses_count.values[truthpd],tick_df['compound'].values[truthpd])
                tickTwitterSeries.followersPositiveWeight.values[ts_idx-1] = np.dot(tick_df.followers_count.values[truthpd],tick_df.positive.values[truthpd])
                tickTwitterSeries.negative.values[ts_idx-1]          = np.sum(tick_df['compound'].values[truthpd] < 0)
                tickTwitterSeries.positive.values[ts_idx-1]          = np.sum(tick_df['compound'].values[truthpd] > 0)
                tickTwitterSeries['compound_score'].values[ts_idx-1] = np.sum(tick_df['compound'].values[truthpd])
                tickTwitterSeries.number.values[ts_idx-1]            = np.sum(truthpd.astype(int))
        print("\t%s Twitter data has been processed"%(tick))
        # Fill in NaN values appropriately
        for header in cols:
            tickTwitterSeries[header].fillna(method='ffill', inplace=True) # most recent val
        # place tick tweet data in dict
        discretetwitterSeries[tick] = tickTwitterSeries
    return discretetwitterSeries

def discretizeCryptoData(cryptoDataFULL,t,shiftwindow  = 60*6):
    """
    Discretize Crypto Data
    """
    # create discretization mask
    mask     = np.arange(len(t))
    mask     = list(np.full_like(mask, np.nan, dtype=np.double))
    ticker   = ['BTC','ETH','LTC','XRP']
    # intialize dictionaries
    discreteCryptoSeries = dict()
    pgain = dict()
    # Train / Test
    cryptoX_array = dict()
    cryptoY_array = dict()
    # Create time range to process
    timesteps = t.copy()
    timesteps.append(timesteps[-1]+1)
    for tick in ticker: # Cycle through tick parameters
        # create a new discrete dataframe
        discreteData = pd.DataFrame({'LASTUPDATE': t,
                                 'PRICE' : mask,
                                 'LASTVOLUME': mask,   # unit crypto currency
                                 'LASTVOLUMETO': mask, # USD value
                                 'OPEN24HOUR': mask,
                                 'HIGH24HOUR': mask,
                                 'LOW24HOUR': mask})
        # retrieve tick data and find idices of matching elements
        tickData = cryptoDataFULL[cryptoDataFULL['FROMSYMBOL'].isin([tick])]
        tickData = tickData.drop_duplicates(subset='LASTUPDATE',keep='last')
        cols = [c for c in discreteData.columns if c is not 'LASTUPDATE']
        for ts_idx in range(1,len(timesteps)):
            # Match timestep indices
            truthpd  = (tickData.LASTUPDATE.values >= timesteps[ts_idx-1]) & (tickData.LASTUPDATE.values < timesteps[ts_idx])
            if truthpd.any():
                for header in cols:
                    # fill in recorded values
                    discreteData[header].values[ts_idx-1]        = np.mean(tickData[header].values[truthpd])
        # fill NaN with 0 for volumns
        discreteData['LASTVOLUME'].fillna(value=0, inplace=True)
        discreteData['LASTVOLUMETO'].fillna(value=0, inplace=True)
        discreteData['WgtPx'] = discreteData.LASTVOLUMETO/discreteData.LASTVOLUME # value/volume
        for header in cols:
            # fill NaN with last value for everything else
            discreteData[header].fillna(method='ffill', inplace=True)

        # Extract signal properties on rolling window
        rollingvaluesShort            = discreteData.PRICE.rolling(window=shiftwindow)
        rollingvaluesLong             = discreteData.PRICE.rolling(window=shiftwindow*3)
        rollingchangesShort           = tickData.PRICE.diff().rolling(window=shiftwindow)

        discreteData['RollingMin']         = rollingvaluesShort.min()                  # Low
        discreteData['RollingMax']         = rollingvaluesShort.max()                  # High
        discreteData['RollingClose']       = rollingvaluesShort.apply(lambda x: x[-1]) # Close
        discreteData['RollingOpen']        = rollingvaluesShort.apply(lambda x: x[0])  # Open
        discreteData['RollingMeanShort']   = rollingvaluesShort.mean()                 # 6hr
        discreteData['RollingMeanLong']    = rollingvaluesLong.mean()                  # 18hr
        discreteData['RS']                 = rollingchangesShort.apply(lambda x: np.mean(x[x > 0])/-np.mean(x[x < 0]))

        # Feature Engineer
        df_Xt =  pd.DataFrame({'LASTUPDATE': t})
        discreteData['V']           = discreteData.RollingMeanShort.diff()
        discreteData['MACD']        = discreteData['RollingMeanShort'] - discreteData['RollingMeanLong']
        discreteData['MACD']        = discreteData['MACD'].rolling(window=int(shiftwindow * 1/3)).mean() # over/under value indicator
        discreteData['Volatility']  = rollingvaluesShort.std() * np.sqrt(shiftwindow) # Calculate the volatility
        # X-features [V,RSI,k,PROC,Volatility,HO,LO,CO,WO]
        df_Xt['V']                  = discreteData['V']
        # RSI --> momentum Relative Strength Index
        df_Xt['RSI']                = 100 - (100 / (1 + discreteData['RS']))
        df_Xt['RSI'].fillna(method='ffill', inplace=True)
        # K --> momentum stochastic oscillator
        df_Xt['k']                  = 100 * (discreteData['RollingClose'] - discreteData['HIGH24HOUR']) / (discreteData['HIGH24HOUR'] - discreteData['LOW24HOUR'])
        df_Xt['PROC']               = discreteData['RollingClose'] - discreteData['RollingClose'].shift(-shiftwindow)
        df_Xt['MACD']               = discreteData['MACD']
        df_Xt['Volatility']         = discreteData['Volatility']
        df_Xt['HO']                 = discreteData['RollingMax'] - discreteData['RollingOpen']
        df_Xt['LO']                 = discreteData['RollingMin'] - discreteData['RollingOpen']
        df_Xt['CO']                 = discreteData['RollingClose'] - discreteData['RollingOpen']
        df_Xt['WO']                 = discreteData['WgtPx'] - discreteData['RollingOpen']

        cryptoX_array[tick] = df_Xt   # xlabel (9 fields)
        # Y Label: categorize price shifts
        discreteData['V+1'] = discreteData['V'].shift(-1)
        UP  =  discreteData['V+1'] > np.std(discreteData['V+1'])
        DN  =  discreteData['V+1'] < -np.std(discreteData['V+1'])
        FLAT  = (UP.astype(int) == 0) & (DN.astype(int) == 0)

        df_Yt =  pd.DataFrame({'LASTUPDATE': t,
                              'UP': UP.astype(int),
                              'DN': DN.astype(int),
                              'FLAT': FLAT.astype(int),
                               'V+1': discreteData['V+1'].values
                              })
        cryptoY_array[tick] = df_Yt  # y label (hot-encoded labels + continuous data)
        # Place pandas Dataframe in dict
        discreteCryptoSeries[tick] = discreteData
        print("\t%s Crypto data has been processed"%(tick))
    return discreteCryptoSeries,cryptoX_array,cryptoY_array

def postprocessXData(cXdf,gdf,tdf,tick):
    """
        postprocessing of feature set (add social data)
    """
    library = {'BTC':'bitcoin','ETH':'ethereum','LTC':'litecoin','XRP':'ripple'}
    outDF = cXdf[tick].copy()
    outDF = outDF.join(gdf[library[tick]].diff())       # detrended google queries
    outDF = outDF.join(tdf[tick].followersCompoundWeight) # weighted compound score
    outDF = outDF.join(tdf[tick].negative)                # sum of overall negative tweets
    outDF = outDF.join(tdf[tick].positive)                # sum of overall positive tweets
    outDF = outDF.join(tdf[tick].compound_score)          # sum compound score
    outDF.rename(columns={library[tick]:'gquery'}, inplace = True)
    return outDF

# Timing functions
def createTimeRange(begin,end,ts = 1):
    """
    create absolute time frame for all data
    """
    dt = end - begin
    timelist = [int(begin + i*ts) for i in range(0,dt//ts)]
    return timelist

def date_to_timestamp(date):
    """
        Return Timestamp from datetime
    """
    # format input string if only date but no time is provided
    if len(date) == 10:
        date = "{} 00:00:00".format(date)
    return [time.mktime(time.strptime(ts, '%Y-%m-%d %H:%M:%S')) for ts in date] #
"""
    Main function:
    1) Load financial and social data.
    2) Discretize data into 1-min bins.
    3)
"""
def main(argv):
    global regexp,ticker

    if len(argv) == 1:
        path =  argv[0]
    else:
        raise ValueError("Arg1 must be the path of raw Data")
    # Load Data
    cryptoDataFULL = retrieveRawCryptoData(path) # raw crypto
    twitterDataFULL = retrieveRawTwitterData(path) # raw twitter
    googleDataFULL = retrieveRawGoogleData(path) # raw google
    # Create range of timestamps
    begin = cryptoDataFULL.LASTUPDATE.values[0]
    end    = cryptoDataFULL.LASTUPDATE.values[-1]+1
    t         = createTimeRange(begin,end,ts = 60) # 60 seconds
    # Synchronize/Discretize Data
    preProcessedPath = path + '/processedData/'
    # 1. Google Data
    discretegoogleSeries = discretizeGoogleData(googleDataFULL,t)
    # 2. Twitter Data
    discretetwitterSeries = discretizeTwitterData(twitterDataFULL,t)
    # 3. Crypto Data
    discreteCryptoSeries,cryptoX_array,cryptoY_array = discretizeCryptoData(cryptoDataFULL,t,shiftwindow  = 60*6)

    # Save discrete data

    discreteFilePath = path + '/processedData/'
    print("Saving discretized data to %s"%(discreteFilePath))
    # Google
    discretegoogleSeries.to_csv(discreteFilePath + 'discreteGOOGLE.csv')
    # Twitter/Crypto
    for tick in ticker:
        discreteCryptoSeries[tick].to_csv(discreteFilePath + tick + 'discreteCRYPTO.csv')
        discretetwitterSeries[tick].to_csv(discreteFilePath + tick + 'discreteTwitter.csv')

    # Save features in postprocessed folder.
    postProcessedPath = path + '/postprocessedData/'
    for tick in ticker:
        outXdf = postprocessXData(cryptoX_array,discretegoogleSeries,discretetwitterSeries,tick)
        # save data
        outXdf.to_csv(postProcessedPath + tick + 'cryptoX_array.csv')
        cryptoX_array[tick] = outXdf
        cryptoY_array[tick].to_csv(postProcessedPath + tick + 'cryptoY_array.csv')

if __name__ == "__main__" :
    main(sys.argv[1:])
