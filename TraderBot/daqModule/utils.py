import json
import time
import requests
from datetime import datetime, timedelta

"""
Utility functions for web/datetime
"""


def build_url(arg, **kwargs):
    """
        Construct a url to request specific API information

        Output:
        --------------------------
        out_url: [str] output url string

        Parameters:
        --------------------------
        arg: [str] API command
        *kwargs: [dict] additional parameters for API
    """
    out_url = None
    # Coinlist finder
    if arg == 'coinlist':
        base_url = 'https://www.cryptocompare.com/api/data/{}/'
        out_url = base_url.format(arg)
    # Price finder
    if arg == 'price' or arg == 'pricemulti' or arg == 'pricemultifull' or arg[:5] == 'histo':
        out_url = _price_finder_helper(arg, **kwargs)
    return out_url


def _price_finder_helper(arg, **kwargs):
    """
        All-in-one helper function for price url constructor
    """
    # Swich key from price to pricemulti (for consistent format)
    base_url = 'https://min-api.cryptocompare.com/data/{}'
    if arg == 'price':
        arg = arg + 'multi'
    out_url = base_url.format(arg)
    # Defining crypto currency
    if 'fsym' in kwargs:
        kval = kwargs['fsym']
    elif 'fsyms' in kwargs:
        kval = kwargs['fsyms']
    key = 'fsyms'
    # Error correction protocol
    if arg[:5] == 'histo':
        key = 'fsym'
    out_url = out_url + '?' + key + '=' + kval
    # Defining fiat conversion currency
    if 'tsyms' in kwargs:
        out_url = out_url + '&tsyms=' + kwargs['tsyms']
    elif 'tsym' in kwargs:
        out_url = out_url + '&tsym=' + kwargs['tsym']
    # For histo
    if arg[:5] == 'histo':
        # Defining the exchange channel
        if 'e' in kwargs:
            out_url = out_url + '&e=' + kwargs['e']
        # Defining the aggregate value
        if 'aggregate' in kwargs:
            out_url = out_url + '&aggregate=' + kwargs['aggregate']
        # Defining the limit value
        if 'limit' in kwargs:
            out_url = out_url + '&limit=' + str(kwargs['limit'])

    return out_url


def get_contents(url):
    """
        Return contents from url

        Output:
        --------------------------
        cont: [dict] contents from url

        Parameters:
        --------------------------
        url: [str] url
    """
    doc = requests.get(url)
    cont = doc.json()
    status = doc.status_code
    return cont, status


def get_coinInfo(coinlist, params=None):
    """
        Return information about User specified crypto-currency

        Output:
        --------------------------
        output: [dict] list of crypto-currencies with associated field values
        params: [list] parameters requested

        Parameters:
        --------------------------
        coinlist: [list] list of crypto-currency indicies
        params: [list] requested information to be returned

    """
    # Initialize Output Dictionary
    output = dict()
    # Retrieve content for all crypto currency
    out_url = build_url(opt[2])
    content = get_contents(out_url)
    # iterate through coinlist to return data matching params
    for ic in coinlist:
        if ic in content['Data']:
            if params is None:
                output[ic] = [content['Data'][ic][kval] for kval in content['Data'][ic].keys()]
                params = content['Data'][ic].keys()
            else:
                output[ic] = [content['Data'][ic][kval] for kval in content['Data'][ic].keys() if kval in params]
    return output, params


def get_HistoricalData(params=None, **kwargs):
    """
        Return price conversion about User specified crypto-currency in discrete time range

        Output:
        --------------------------
        output: [dict] list of crypto-currency price over discrete time range
               (price,ts)

        Parameters:
        --------------------------
                  params    = [list,str] = parameters to store (default is ALL)
        **kwargs  fsym      = [str] crypto-currency
                  tsym      = [str] conversion currencies
                  freq      = [str] 'day','hour',minute' (frequency of price info requested)
                  aggregate = [int] 1 (aggregated estimate of price info requested)
                  e         = [str] exchange market (default -->'CCCAGG')
                  limit     = [int] Number of values to return (default --> 10)
    """
    # Create parameters for nested historical search
    freq_url = 'histo' + kwargs['freq']
    # Select exchange
    if 'e' not in kwargs:
        kwargs['e'] = 'CCCAGG'
    if 'limit' not in kwargs:
        kwargs['limit'] = 10
    out_url = build_url(freq_url, **kwargs)
    # Retrieve data
    data = get_contents(out_url)
    # convert to dict
    return __list_to_dict(data)


def __list_to_dict(data, params=None):
    klist = data['Data'][0].keys()
    output = dict()
    # Initialize dict with keys with null values
    for k in klist:
        if params is not None and k not in params:
            continue
        output[k] = []
    # Iterate through list to store value in appropriate Dict field
    for entry in data['Data']:
        for k in klist:
            output[k].append(entry[k])
    return output


def timestamp_to_date(time, form='%Y-%m-%d %H:%M:%S'):
    """
        Return Timestamp from datetime

        Output:
        --------------------------
        output: [Datetime]

        Parameters:
        --------------------------
        ts:  [timestamp]
    """
    return [datetime.fromtimestamp(int(ts)).strftime(form) for ts in time]


def timestamp_to_datetime(time):
    return [datetime.fromtimestamp(ts) for ts in time]


def date_to_timestamp(date):
    """
        Return Timestamp from datetime

        Output:
        --------------------------
        output: [timestamp]

        Parameters:
        --------------------------
        date: Date as string with these formats: "Y-m-d", "Y-m-d H-M-S".
    """
    # format input string if only date but no time is provided
    if len(date) == 10:
        date = "{} 00:00:00".format(date)

    return time.mktime(time.strptime(date, '%Y-%m-%d %H:%M:%S'))


def loadCredentials(fname):
    with open(fname, 'r') as f:
        line = f.readline()
        code = []
        res = []
        while line:
            val = line.strip().split(',')
            code.append(val[0])
            res.append(val[1])
            line = f.readline()
    return code, res
