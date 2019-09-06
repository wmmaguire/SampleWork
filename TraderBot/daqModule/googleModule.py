# libs
# Google Trends
from pytrends.request import TrendReq
# Libs for timing/threading
import time
from datetime import datetime, timedelta
import threading
# SQL libs
import pymysql
from sqlalchemy import create_engine
# libs for file storage
import os
import csv
import pandas as pd
import numpy as np
import math
"""Main class"""


class GtrendsStreamer():
    """
    Google streamer to return normalized keyword queries (per minute every hour)
    """

    def __init__(self, keywords=['bitcoin'], path='', dt=3480, timeframe='now 1-H', writeToCsv=True, delay=30):
        # Google query parameters
        self.pytrend = TrendReq()
        self.keywords = keywords
        # Set timing parameters
        self.queryDelay = 0.5   # Don't spam google with requests or it will error out
        self.interval = delay
        self.time_begin = datetime.now()
        self.curTime = time.time()
        self.prevTime = self.curTime
        self.dt = dt  # condition to query google (default: 360 seconds)
        # Data Storage
        self.timeframe = timeframe
        self.prevLoggedDF = None
        self.Gwritten = 0
        self.writeToCsv = writeToCsv
        if self.writeToCsv:
            self.path = self.__setCSVpath(path)
        else:
            self.sqlInfo = {'host': "localhost", 'usr': "root", 'passwrd': "", 'db': "crypto_data"}
            self.__setupSQLcomm()
        # For safe stop
        self.stopFlag = True
        # set-up threading task
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        """
        Method that retrieves data from crypto compare at preset interval
        """
        while self.stopFlag:
            # Update Timer
            self.curTime = time.time()
            # retrieve google trends data if dt exceeded
            if (self.curTime - self.prevTime) >= self.dt:
                try:
                    res = self.queryGoogleTrends()
                    # Write to database
                    if self.writeToCsv:
                        self.write_to_csv(res)
                    else:
                        self.write_to_mySQL(res)
                    # Update dt and Index count
                    self.Gwritten += len(res.index)
                    self.prevTime = self.curTime
                    #print('Google Trends Index length: %d'%(self.Gwritten))
                except BaseException as e:
                    # Error handling
                    print('Google failed on run,', str(e))
                    # self.safeShutDown()
            time.sleep(self.interval)  # wait for time interval (default: 30s)
        # One last google trends retrieval before shutting off
        res = self.queryGoogleTrends()
        if self.writeToCsv:
            self.write_to_csv(res)
        else:
            self.write_to_mySQL(res)
        print("Closing Google Trend Stream: ", self.curTime)

    def queryGoogleTrends(self):
        """
        Cycle through keywords to return normalized results of keyword queries and append to dataframe
        """
        # Initialize local variables
        res = pd.DataFrame()
        boolidx = 0
        for i, key in enumerate(self.keywords):
            self.pytrend.build_payload(kw_list=[key], timeframe=self.timeframe)
            temp_res = self.pytrend.interest_over_time()
            # Convert to EST
            temp_res.index = temp_res.index - timedelta(hours=4)
            # Drop irrelevant column
            temp_res.drop('isPartial', axis=1, inplace=True)
            # convert to float
            temp_res[key] = temp_res[key].astype(float)
            # Apply rescaling
            (temp_res, boolidx) = self.__applyPCRatio(key, temp_res)
            if i == 0:
                res = temp_res
            else:
                res = res.join(temp_res)
            # NOTE: Don't spam google with requests or it will error out with code 429
            time.sleep(self.queryDelay)  # Default[0.5 second delay]
        # Store current query result and return rescaled value for data storage
        self.prevLoggedDF = res
        return res.iloc[-boolidx:]

    def __applyPCRatio(self, key, cur):
        """
        Method to offset scale all subsequent normalized trend data based on previous reading
        """
        boolidx = 0
        pcRatio = 1
        # Base case 1: (return current ratio)
        if self.prevLoggedDF is not None:
            # Find index of first match
            boolarray = cur.index[0] == self.prevLoggedDF.index
            boolidx = np.argmax(boolarray.astype(int))
            # compute offset ratio (excluding inf or nan values)
            temp_pcRatio = cur[key][:-boolidx] - self.prevLoggedDF[key][boolidx:]
            temp_pcRatio = [rat for rat in temp_pcRatio if not math.isinf(rat) if not math.isnan(rat)]
            if temp_pcRatio:
                pcRatio = np.mean(temp_pcRatio)
            else:
                pcRatio = 1
        # apply ratio and return new values
        return (cur - pcRatio, boolidx)

    def write_to_csv(self, tempSeriesData):
        """
        Method to dump series data into csv file
        """
        # if file does not exist write header
        if not os.path.isfile(self.path):
            print('Creating new file: %s' % (self.path))
            tempSeriesData.to_csv(self.path, header=True, encoding='utf-8')
        else:  # else it exists so append without writing the header
            tempSeriesData.to_csv(self.path, mode='a', header=False, encoding='utf-8')
        return

    def write_to_mySQL(self, tempSeriesData):
        """
        Method to dump series data into SQL Table
        """
        # re-Create table if already exists
        if self.Gwritten == 0:
            print('Creating new Google Trend SQL table: %s' % (self.path))
#        else: # else it exists so append without writing the header
        # Adjust dataframe and write to sql table
        tempSeriesData.to_sql(self.path, self.engine, if_exists='append', index=False)
        return

    def __setCSVpath(self, path):
        """
        Initialize csv data path
        """
        #print("Initialize CSV file: ",begin_ts)
        begin_ts = self.time_begin.strftime("-%Y_%m_%d-%H_%M_%S")
        keywords = '_'.join(self.keywords)
        path += 'GoogleTrends-' + keywords + begin_ts + '.csv'
        return path

    def __setupSQLcomm(self):
        """
        Initializel mysql data path
        """
        # Store local variables
        host = self.sqlInfo['host']
        usr = self.sqlInfo['usr']
        password = self.sqlInfo['passwrd']
        db = self.sqlInfo['db']
        # Open database connection
        self.conn = pymysql.connect(host=host, user=usr, passwd=password, db=db)
        # prepare a cursor object using cursor() method
        self.cursor = self.conn.cursor()
        # Engine to access sql via python
        self.mysqlDB_url = 'mysql+pymysql://' + usr + ':' + password + '@' + host + '/' + db
        self.engine = create_engine(self.mysqlDB_url)
        # Intialize SQL table name
        begin_ts = self.time_begin.strftime("__%Y_%m_%d__%H_%M_%S")
        self.path = 'GoogleTrends__' + begin_ts

    def safeShutDown(self):
        self.stopFlag = False
