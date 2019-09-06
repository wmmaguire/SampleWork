# Tweepy streamer
import tweepy
from tweepy.streaming import StreamListener
from urllib3.exceptions import ProtocolError
# NLP lib
import nltk
import re
# Tim libs
from datetime import datetime
import time
# SQL libs
import pymysql
from sqlalchemy import create_engine
# file storage tools
import json
import os
import csv
import pandas as pd
"""
Twitter Helper functions
"""
#Override tweepy.StreamListener to add logic to on_data
class listener(StreamListener):
    """
    Subclass of streamListener to log Twitter/sentiment data
    """
    def __init__(self, start_time, wait = 0.1, time_limit=20,sqlInfo = None,api = None):
        self.api  = api
        self.time  = start_time
        self.limit = time_limit
        self.wait  = wait
        self.stopFlag  = True
        self.prevStatusObj = None

    def configureTweetHandler(self,tweet_handler):
        self.tweet_handler = tweet_handler

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False

    def on_status(self, status):
        # Retrieve data over set time period
        while ((time.time() - self.time) < self.limit) and self.stopFlag:
            # Ignore repeated tweets
            if self.prevStatusObj == status:
                return
            try:
                # Log data into params
                params = {'created_at':None,'id_str':None,'text':None,
                          'followers_count':None,'statuses_count':None,'friends_count':None }
                params['text']            = status.text
                params['created_at'] = status.timestamp_ms
                params['id_str']         = status.user.name
                params['followers_count'] = status.user.followers_count
                params['statuses_count']  = status.user.statuses_count
                params['friends_count']     = status.user.friends_count
                # Enqueue buffer
                self.tweet_handler.enqueueBuffer(params)
                # Log twitter/sentiment data to csv
                if self.tweet_handler.cnt > 0 and self.tweet_handler.cnt % self.tweet_handler.buffer_size == 0:
                    self.tweet_handler.bufferDumptoStorage()
            except BaseException as e:
                # method to reset stream from tweet handler
                print('Twitter failed on status:\t',self.time)
                print(str(e))
                time.sleep(self.wait)
                self.tweet_handler.setError(state=True)
            self.prevStatusObj = status

    def on_error(self, status_code):
        if status_code == 420:
            self.tweet_handler.setError(state=True)
            #returning False in on_data disconnects the stream
            return False

    def safeShutDown(self):
        self.stopFlag = False


"""
Twitter handler and stream buffer
"""
class tweet_handler():
    """
    Twitter stream handler:
    - Buffer
    - error handler
    - NLP sentiment analyzer
    - data storage
    """
    def __init__(self,path='',keywords = [''],BUFFER_SIZE = 20,NLP_tool=None,sqlInfo=None,writeTweet=True):
        # Initialize error handler
        self.tError = False
        # Initialize instance variables
        self.cnt        = 0
        self.twritten   = 0
        # Initialize twitter params
        self.writeTweet     = writeTweet
        self.keywords       = keywords
        self.buffer_size    = BUFFER_SIZE
        self.tweet_queue    = tweet_buffer()
        # Initialize NLP tool
        self.regexp = re.compile('[^a-zA-Z]')
        self.NLP_tool = NLP_tool
        if self.NLP_tool is None:
            self.sentimentLabels = ['polarity','subjectivity','classification']
        else:
            self.sentimentLabels = ['negative','neutral','positive','compound']
        # Initialize database file
        self.time_begin = datetime.now()
        self.cryptoSync = self.time_begin
        self.sqlInfo  = sqlInfo
        if self.sqlInfo is not None:
            self.__setupSQLcomm()
        else:
            self.path       = self.__setCSVpath(path)

    def getHandleError(self):
        """
        Use to continually check state of stream.  If false, reset stream.
        """
        return self.tError,self.path

    def setCryptoSync(self,time):
        # Not used..
        self.cryptoSync = time

    def enqueueBuffer(self,params):
        """
        enqueue buffer
        """
        self.cnt        += 1
        self.tweet_queue.enqueue(params)

    def bufferDumptoStorage(self):
        """
        Dump tweet_buffer data to csv file.
        """
        dumpSize = self.tweet_queue.size
        # Dump queue data to csv
        if dumpSize > 0:
            if self.sqlInfo is not None:
                self.write_to_mySQL(self.tweet_queue.dump(),dumpSize)
            else:
                self.write_to_csv(self.tweet_queue.dump(),dumpSize)
            self.twritten   += dumpSize
            #print('\tTwitter Index length: %d'%(self.twritten))

    def dequeueBuffer(self,size=1):
        """
        dequeue tweet_buffer data
        """
        if self.tweet_queue.size <= size:
            return self.tweet_queue.dequeue(size)
        return None

    def write_to_csv(self,dataDump,dumpSize):
        """
        Method to dump buffered series data (including sentiment analysis) into csv file
        """
        # Apply Sentiment Analysis
        dataDump = self.SentimentAnalysis(dataDump,dumpSize)
        # Convert into pandas Dataframe
        tempSeriesData = pd.DataFrame.from_dict(dataDump,orient = 'columns')
        tempSeriesData.index = range(self.twritten,self.twritten+dumpSize)
        if not self.writeTweet:
            tempSeriesData.drop('text', axis=1, inplace=True)
        # if file does not exist write header
        if not os.path.isfile(self.path):
            print('Creating new file: %s'%(self.path))
            tempSeriesData.to_csv(self.path,header = True,encoding='utf-8')
        else: # else it exists so append without writing the header
            tempSeriesData.to_csv(self.path,mode = 'a',header=False,encoding='utf-8')
        return

    def write_to_mySQL(self,dataDump,dumpSize):
        """
        Method to dump buffered series data (including sentiment analysis) into SQL Table
        """
        # Apply Sentiment Analysis
        dataDump = self.SentimentAnalysis(dataDump,dumpSize)
        # Convert into pandas Dataframe
        tempSeriesData = pd.DataFrame.from_dict(dataDump,orient = 'columns')
        # re-Create table if already exists
        if self.twritten == 0:
            print('Creating new SQL table: %s'%(self.path))
 #       else: # else it exists so append without writing the header
        # Adjust dataframe and write to sql table
        tempSeriesData.drop(['id_str', 'text'], axis=1, inplace=True)
        tempSeriesData.to_sql(self.path, self.engine, if_exists='append', index=False)
        return

    def SentimentAnalysis(self,dictData,dictSize):
        """
        Extend dict data to include sentiment analysis
        """
        # Populate dict with keyword
        dictData['keyword'] = []
        # Populate dict with labels
        for label in self.sentimentLabels:
            dictData[label] = []
        # Conduct sentiment analysis
        for idx in range(dictSize):
            tweet_text = dictData['text'][idx]
            # Log the keyword that was captured
            keywords = [key for key in self.keywords if key.lower() in self.__cleanString(tweet_text)]
            dictData['keyword'].append(",".join(keywords))
            # Check sentiment analysis method
            if self.NLP_tool is None:
                analysis  = TextBlob(tweet_text)
                # {'polarity', 'subjectivity', 'classification'}
                dictData[self.sentimentLabels[0]].append(analysis.sentiment.polarity)
                dictData[self.sentimentLabels[1]].append(analysis.sentiment.subjectivity)
                dictData[self.sentimentLabels[2]].append(classify_sentiment(analysis))
            else:
                analysis = self.NLP_tool.polarity_scores(tweet_text)
                # {'neg', 'neu', 'pos', 'compound'}
                dictData[self.sentimentLabels[0]].append(analysis['neg'])
                dictData[self.sentimentLabels[1]].append(analysis['neu'])
                dictData[self.sentimentLabels[2]].append(analysis['pos'])
                dictData[self.sentimentLabels[3]].append(analysis['compound'])
        return dictData

    def __cleanString(self,txt):
        """
        Clean string to find keywords
        """
        return self.regexp.sub(" ",txt.lower()).split()

    def __setCSVpath(self,path):
        """
        Initialize data path
        """
        # Base case 1: res
        if '.csv' in path:
            return path
        begin_ts  = self.time_begin.strftime("-%Y_%m_%d-%H_%M_%S")
        keywords  = '_'.join(self.keywords)
        path      += 'Twitter-' + keywords + begin_ts + '.csv'
        return path

    def __setupSQLcomm(self):
        # Store local variables
        host     = self.sqlInfo['host']
        usr      = self.sqlInfo['usr']
        password = self.sqlInfo['passwrd']
        db       = self.sqlInfo['db']
        # Open database connection
        self.conn = pymysql.connect(host=host,user=usr,passwd=password,db=db)
        # prepare a cursor object using cursor() method
        self.cursor = self.conn.cursor()
        # Engine to access sql via python
        self.mysqlDB_url = 'mysql+pymysql://'+ usr + ':' + password + '@' + host + '/' + db
        self.engine = create_engine(self.mysqlDB_url)
        # Intialize SQL table name
        begin_ts  = self.time_begin.strftime("__%Y_%m_%d__%H_%M_%S")
        #keywords  = '_'.join(self.keywords)
        self.path = 'Twitter__stream' + begin_ts

    def setError(self,state=False):
        self.tError = state

class tweet_buffer():
    """
    Buffer of tweet info Dict of lists [keys=self.labels]
    """
    def __init__(self):
        self.size       = 0
        self.labels     = ['created_at','id_str','text','followers_count',
                           'statuses_count','friends_count']
        self.bufferedDict = {k: [] for k in self.labels}

    def enqueue(self,params):
        """
        Push data to buffer (Set to 1)
        """
        for key in params:
            # Store unit Data
            self.bufferedDict[key].append(params[key])
        # increment size
        self.size    += 1

    def dequeue(self,size=1):
        """
        dequeue data from queue (by size)
        """
        temp_dictOut = {k: [] for k in self.labels}
        for key in self.bufferedDict:
            # Store variables locally
            temp_dictOut[key] = self.bufferedDict[key][:size]
            # Flush select data
            self.bufferedDict[key] = self.bufferedDict[key][size:]
        # reset size
        self.size       -= size
        return temp_dictOut

    def dump(self):
        """
        Dump all data from queue
        """
        temp_dictOut = {k: [] for k in self.labels}
        for key in self.bufferedDict:
            # Store variables locally
            temp_dictOut[key] = self.bufferedDict[key]
            # Flush data
            self.bufferedDict[key] = []
        # reset size
        self.size       = 0
        return temp_dictOut
    ##
