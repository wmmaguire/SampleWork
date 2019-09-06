from utils import build_url, get_contents
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

"""
Crypto Web scraper: Class object
"""


class AsynchronousCryptoCompareDAQ(object):
    """
    Asynchronous Crypto Ticker Using Crypto Compare API wrapper
    The run() method will be started and it will retrieve full ticker data
    in the background until the application exits.
    """

    def __init__(self, opt='pricemultifull', fsyms=['BTC'],
                 tsyms='USD', interval=0.1, writeToCsv=False, path='', binSize=2):
        """
        Parameters:
             opt:     [str] - api call
             fsyms:   [str] - crypto currency (only supports one for now)
             tsyms:   [str] - Fiat currency conversion (only supports one for now)
             interval [int] Data retrieval interval (seconds)
        """
        # Wrapper parameters
        self.interval = interval
        self.opt = opt
        self.fsyms = fsyms
        self.tsyms = tsyms
        # Data acquisition metrics
        self.Flag = True
        self.cntr = 0
        self.time_begin = datetime.now()
        self.timer = self.time_begin
        # Buffer params
        self.seriesSize = 0
        self.df = pd.DataFrame()
        self.seriesData = {}
        self.getDataBlockingCall = False
        # Data Storage
        self.writeToCsv = writeToCsv
        if self.writeToCsv:
            self.path = self.__setCSVpath(path)
        else:
            self.sqlInfo = {'host': "localhost", 'usr': "root", 'passwrd': "", 'db': "crypto_data"}
            self.__setupSQLcomm()
        self.binSize = binSize
        # set-up threading task
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        """
        Method that retrieves data from crypto compare at preset interval
        """
        ddata = dict()
        while self.Flag:
            # Update Timer
            self.timer = datetime.now()
            # Retrieve Crypto Data for each currency listed
            fsym = ','.join(self.fsyms)
            out_url = build_url(self.opt, fsyms=fsym, tsyms=self.tsyms)
            try:
                cont, status = get_contents(out_url)
                if status == 200:
                    for fsym in self.fsyms:
                        ddata[fsym] = cont['RAW'][fsym][self.tsyms]
                        ddata[fsym]['ScrapeTime'] = self.timer.timestamp()
                    # On first call initialize series variable and append subsequent entries
                    while self.getDataBlockingCall:
                        print('Blocking Call...\n')
                        time.sleep(self.interval)
                        pass
                    temp_df = pd.DataFrame.from_dict(ddata, orient='index')

                    # Re-index pandas dataframe and keep unique values
                    self.df = self.df.append(temp_df)
                    self.df.index = range(len(self.df.index))
                    temp_df = pd.DataFrame()
                    # eliminates duplicates (condider deleting this)
                    for fsym in self.fsyms:
                        iloc = self.df.index[self.df['FROMSYMBOL'] == fsym]
                        temp_df = temp_df.append(self.df.loc[iloc].drop_duplicates(subset='LASTUPDATE', keep='last'))
                    # Update series info
                    self.df = temp_df
                    self.df.index = range(0, len(self.df.index))
                    # Automated way of logging data to CSVfile
                    if self.binSize < len(self.df.index):
                        SeriesData_dump = self.getData(peek=False)
                        if self.writeToCsv:
                            self.writeToCSVfile(SeriesData_dump)
                        else:
                            self.writeToMySQL(SeriesData_dump)
                        #print('\tCrypto Index length: %d'%(self.seriesSize))
                    # Update timer and counters
                    self.cntr += 1
                else:
                    print("Error retrieving data: %d" % (status))
            except BaseException as e:
                # Error handling
                print('Crypto failed ondata:\t', self.timer)
                print(str(e))
            time.sleep(self.interval)  # wait for time interval (default: 0.1s)
        if len(self.df.index) > 0:
            SeriesData_dump = self.getData(peek=False)
            if self.writeToCsv:
                self.writeToCSVfile(SeriesData_dump)
            else:
                self.writeToMySQL(SeriesData_dump)
        print("Closing Crypto threaded Task: ", self.timer)

    def getData(self, peek=False):
        """
        Method to access data within main application
        """
        tempSeriesData = None
        if len(self.df) > 0:
            self.getDataBlockingCall = True  # Blocking mutex
            if not peek:
                self.df.index = range(self.seriesSize, self.seriesSize + len(self.df.index))
                self.seriesSize += len(self.df.index)
                tempSeriesData = self.df   # Retrieve buffered series data
                self.df = pd.DataFrame()   # reset df
            self.getDataBlockingCall = False  # Unblock
        return tempSeriesData

    def writeToCSVfile(self, tempSeriesData):
        """
        Method to dump buffered series data into csv file
        """
        # if file does not exist write header
        if not os.path.isfile(self.path):
            print('\tCreating new file: %s' % (self.path))
            tempSeriesData.to_csv(self.path, header=True)
        else:  # else it exists so append without writing the header
            tempSeriesData.to_csv(self.path, mode='a', header=False)
        return

    def writeToMySQL(self, dataDump):
        """
        Method to dump buffered series data into SQL Table
        """
        # re-Create table if already exists
        if dataDump.index[0] == 0:
            print('Creating new SQL table: %s' % (self.path))
#        else: # else it exists so append without writing the header
        # Adjust dataframe and write to sql table
        dataDump.to_sql(self.path, self.engine, if_exists='append', index=False)
        return

    def __setCSVpath(self, path):
        """
        Initialize data path
        """
        begin_ts = self.time_begin.strftime("-%Y_%m_%d-%H_%M_%S")
        fsyms = '-'.join(self.fsyms)
        path += fsyms + begin_ts + '.csv'
        return path

    def __setupSQLcomm(self):
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
        keywords = '_'.join(self.fsyms)
        self.path = 'Crypto__' + keywords.replace(" ", "") + begin_ts

    def safeExit(self, peek=False):
        """
        Method for closing stream
        """
        tempSeriesData = self.getData(peek)
        if self.writeToCsv and tempSeriesData is not None:
            self.writeToCSVfile(tempSeriesData)
        self.Flag = False
        return tempSeriesData
