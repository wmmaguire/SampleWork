# Utility functions
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from keras.models import model_from_json
path = '/Users/maxmaguire/Desktop/PostGradWork/Projects/Data/HistoricalData/HFT_Data/'


def loadProcessedCryptoData(ticker, foldername, dataType='CRYPTO'):
    """
    load processed data
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
    print(datetime.now())
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


def createDataSets(x_df, train_div, time_step, categorical=False):
    """
    configure labeled data to predict price value UP TO time_step in the future
    """
    # Find index to split data
    N = len(x_df.index)  # supervised_data not needed
    train_size = int(N * train_div)

    # create X data
    xtrain, xtest = x_df.values[:train_size], x_df.values[train_size:]
    # Scaling methods: scale data to fit between -1 and 1
    xscaler, xtrain_scaled, xtest_scaled = scale(xtrain, xtest)

    # create Y data

    yscaler, ytrain_scaled, ytest_scaled = scale(x_df.V.values[:train_size], x_df.V.values[train_size:])
    yall_scaled = np.append(ytrain_scaled, ytest_scaled)
    future_data = timeseries_to_supervised(yall_scaled, time_step)
    if categorical:  # Classification
        yout = oneHotEncode(future_data.values[:, -1])
        ytrain_scaled, ytest_scaled = yout[:train_size, :], yout[train_size:-time_step, :]
    else:               # Regression
        ytrain_scaled, ytest_scaled = future_data.values[:train_size, 1:], future_data.values[train_size:-time_step, 1:]

    return (xscaler, xtrain_scaled, xtest_scaled), (yscaler, ytrain_scaled, ytest_scaled)


def timeseries_to_supervised(data, lag=1):
    """
    frame a sequence as a supervised learning problem
    """
    df = pd.DataFrame(data)
    columns = [df.shift(-i) for i in range(1, lag + 1)]
    columns.insert(0, df)
    df = pd.concat(columns, axis=1)
    df.fillna(0, inplace=True)
    df.columns = ["V+" + str(l) for l in range(0, lag + 1)]
    return df


def scale(train, test, frange=(-1, 1)):
    """
    scale train and test data to [-1, 1]
    """
    # fit scaler
    scaler = MinMaxScaler(feature_range=frange)
    # Reshape if only one feature
    if train.ndim > 1:
        train = train.reshape(train.shape[0], train.shape[1])
        test = test.reshape(test.shape[0], test.shape[1])
    else:
        train = train.reshape(-1, 1)
        test = test.reshape(-1, 1)
    # transform train
    scaler = scaler.fit(train)
    train_scaled = scaler.transform(train)
    # transform test
    test_scaled = scaler.transform(test)
    return scaler, train_scaled, test_scaled


def oneHotDecode(y_in):
    return np.argmax(y_in, axis=1)


def oneHotEncode(y_in, tol=None):
    yidx = makeCategorical(y_in)
    ymax = np.max(yidx) + 1
    yout = np.zeros((len(yidx), ymax))
    for i in range(ymax):
        yout[yidx == i, i] = 1
    return yout


def CategoricalAccuracy(model, X, y, ts=0):
    # Comput Categorical Accuracy
    yhat = model.predict(X, batch_size=1)
    # Testing model accurcy
    ypred = oneHotDecode(yhat)
    yreal = oneHotDecode(y)
    # return accuracy
    return np.sum((ypred[:ts] == yreal).astype(int)) / yreal.shape[0]


def makeCategorical(y_in, tol=0.2):
    if tol is None:
        tol = np.std(y_in)
    y_out = np.zeros(y_in.shape, dtype=int)
    y_out[(y_in <= tol) & (y_in >= -tol)] = 1
    y_out[y_in > tol] = 2
    return y_out


def calculatePerformance(yhat, y, method="rms"):
    # root-mean square error
    if method is "rms":
        return np.sqrt(np.power((yhat - y), 2))
    # mean-absolute-percentage-error
    if method is "mape":
        return np.abs((y - yhat) / y) * 100
    # accuracy
    if method is "acc":
        return np.sum((yhat == y).astype(int)) / len(y)


def loadModel(filepath):
    """
    load json and create model
    """
    with open(filepath + ".json", 'r') as json_file:
        loaded_model_json = json_file.read()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights(filepath + ".h5")
    print("Loaded model from ", filepath)
    return loaded_model

# Principle Component Analysis


def pca(X):
    # normalize the features
    X = (X - X.mean()) / X.std()

    # compute the covariance matrix
    X = np.matrix(X)
    cov = (X.T * X) / X.shape[0]

    # perform SVD
    U, S, V = np.linalg.svd(cov)

    return U, S, V


def project_data(X, U, k):
    U_reduced = U[:, :k]
    return np.array(np.dot(X, U_reduced))
