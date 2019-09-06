# Libs
import sys
import time
import os
import math
import tweepy
from utils import loadCredentials
# Import Classes
from CryptoModule import AsynchronousCryptoCompareDAQ
from googleModule import GtrendsStreamer
from twitterModule import listener, tweet_handler
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
# Visualizing progress
import progressbar
bar_widgets = [
    'Training: ', progressbar.Percentage(), ' ', progressbar.Bar(marker="-", left="[", right="]"),
    ' ', progressbar.ETA()
]
###### Global variables #######
# set path of csv file to save sentiment stats
nseconds = 60 * 60 * 24   # 1 days worth of data
path = '/Users/maxmaguire/Desktop/PostGradWork/Projects/Data/HistoricalData/HFT_Data/'


def main(argv):
    global nseconds
    global path
    # base case: must enter a time duration for script to run
    if not (len(argv) >= 1):
        raise ValueError("Arg1 must be a duration of time (days)")
    nseconds *= int(argv[0])  # amount of days to run
    if len(argv) == 2:
        path = argv[1]  # new path

    # load twitter credentials
    code, res = loadCredentials('creds.txt')
    # Initialize Asynchrounous DAQ activities
    # 1: Crypto Compare Scraper
    # Following top 5 crypto-currencies ['BTC', 'ETH', 'BCH', 'LTC', 'OMG', 'XRP']
    fsyms = ['BTC', 'ETH', 'LTC', 'XRP']
    realTime_cryptoticker = AsynchronousCryptoCompareDAQ(fsyms=fsyms, interval=0.3, path=path,
                                                         binSize=len(fsyms) * 5, writeToCsv=True)  # csv or SQL
    fsyms = realTime_cryptoticker.fsyms
    tyms = realTime_cryptoticker.tsyms
    start = realTime_cryptoticker.time_begin.strftime("%Y-%m-%d %H:%M:%S")

    # 2: Twitter Streamer
    keywords1 = ['bitcoin', fsyms[0],
                 'ethereum', fsyms[1],
                 'litecoin', fsyms[2],
                 'Ripple', fsyms[3]]

    # access twitter api via tweepy methods
    auth = tweepy.OAuthHandler(res[0], res[1])
    auth.set_access_token(res[2], res[3])
    # Error handling
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        print('Error! Failed to get request token.')
        return

    # Construct the API instance
    api = tweepy.API(auth)
    print(api.me().name)

    # create tweet handler
    sia = SIA()  # nlp tool

    # Open database connection
    sqlInfo = {'host': "localhost", 'usr': "root", 'passwrd': "", 'db': "crypto_data"}

    # create tweet handlers
    htweets1 = tweet_handler(keywords=keywords1, path=path, BUFFER_SIZE=40, NLP_tool=sia, sqlInfo=None)

    # Set up a socket streams
    start_time = time.time()
    myStreamListener1 = listener(start_time, time_limit=math.inf, api=api)  # indefinitely

    # Configure tweet handlers in socket streams
    myStreamListener1.configureTweetHandler(htweets1)

    # Run socket Stream
    myStream1 = tweepy.Stream(auth=api.auth, listener=myStreamListener1)
    myStream1.filter(languages=["en"], track=keywords1, async=True, stall_warnings=True)

    # 3: Google Streamer
    keywords = ["bitcoin", "ethereum", "litecoin", "ripple"]
    #                                           every 30 minutes, log past hour to file       (60 second delay)
    gt_handle = GtrendsStreamer(keywords=keywords, path=path, dt=60 * 30, timeframe='now 1-H', writeToCsv=True, delay=60)

    # loop to log ticker data for real time analysis
    delay = 1
    tfails = 0
    # To visualize progress
    bar = progressbar.ProgressBar(widget=bar_widgets)
    for _ in bar(range(nseconds)):
        time.sleep(delay)
        (err, p) = htweets1.getHandleError()
        if err:  # reset twitter stream if issue
            tfails += 1
            # shut-down previous stream
            myStreamListener1.safeShutDown()
            time.sleep(0.1)
            myStream1.disconnect()
            print('\tResetting Twitter Data Stream')
            # set-up new stream
            htweets1 = tweet_handler(keywords=keywords1, path=p, BUFFER_SIZE=40, NLP_tool=sia, sqlInfo=None)
            # Set up a socket streams
            start_time = time.time()
            myStreamListener1 = listener(start_time, time_limit=math.inf)  # indefinitely
            # Configure tweet handlers in socket streams
            myStreamListener1.configureTweetHandler(htweets1)
            # Run socket Stream
            myStream1 = tweepy.Stream(auth=api.auth, listener=myStreamListener1)
            myStream1.filter(languages=["en"], track=keywords1, async=True, stall_warnings=True)

    # Safe Shutdown methods
    # 1. Crypto Scraper
    realTime_cryptoticker.safeExit(peek=False)
    # 2. Twitter Streamers
    myStreamListener1.safeShutDown()
    time.sleep(0.2)
    myStream1.disconnect()
    print('Closing Twitter Data Stream')
    # 3. Google Streamer
    gt_handle.safeShutDown()
    return

if __name__ == "__main__":
    main(sys.argv[1:])
