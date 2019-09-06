# import libraries
from lstm_network import lstm_network as lstmNET
from utils import *
import os
import sys
import numpy as np
import pandas as pd


def main(argv):
    # Error checking
    if len(argv) < 3:
        print("\nError: User must input 3 arguments:")
        print("\tArg1: folder")
        print("\tArg2: tick")
        print("\tArg3: time step")
        print("NOTE: multi-variable arguments need to be comma delimited\n")
        return
    # unpack user input
    if len(argv) == 4:
        folder, tick, time_steps, categorical = argv
        categorical = categorical.lower() == 'true'
        dltype = 'Classification'
    else:
        folder, tick, time_steps = argv
        categorical = True
        dltype = 'Regression'
    time_steps = list(map(int, time_steps.split(',')))

    # Load processed feature-set
    x_df, _, _, _ = loadPostProcessedData(folder, tick, dropXLabel=['gquery', 'positive', 'negative', 'compound_score', 'MACD', 'LASTUPDATE'])

    print("Training %s LSTM model with features:" % (dltype))
    print(x_df.columns, "\n")

    # Model Design Parameters
    train_div = 0.7   # train on 70 percent of data

    # generate train/test sets
    ydata = {'TrainScaled': [], 'TestScaled': [], 'scaler': []}
    for time_step in time_steps:
        (_, xTrainScaled, xTestScaled), (y_scaler, yTrainScaled, yTestScaled) = createDataSets(x_df,
                                                                                               train_div,
                                                                                               time_step, categorical=categorical)
        # log x data in dict
        print("V+%d \tytrain shape: " % (time_step), yTrainScaled.shape)
        ydata['TrainScaled'].append(yTrainScaled)
        ydata['TestScaled'].append(yTestScaled)
        ydata['scaler'].append(y_scaler)

    xdata = {'TrainScaled': xTrainScaled,
             'TestScaled': xTestScaled}

    # reshape features space
    Xtrain = xdata['TrainScaled'].reshape(xdata['TrainScaled'].shape[0], 1, xdata['TrainScaled'].shape[1])
    Xtest = xdata['TestScaled'].reshape(xdata['TestScaled'].shape[0], 1, xdata['TestScaled'].shape[1])

    # Model parameters
    batch_size = 1     # Always 1 for online learning
    n_epochs = 250
    lstm_units = 2
    stacks = 1

    # Cycle through step-sizes
    for i in range(0, len(time_steps)):
        print("Training future predict: %d minutes" % (time_steps[i]))
        # Model design
        lstmModel = lstmNET(xdata['TrainScaled'], ydata['TrainScaled'][i], batch_size=1, nb_epoch=300,
                            step_size=1, neurons=2, stacks=stacks, val_split=0.2, classification=categorical, opt='adam')
        # train model
        lstmModel.fit_lstm()
        # Save model
        filename = dltype + 'model' + str(time_steps[i])
        lstmModel.saveModel(filename)

if __name__ == "__main__":
    main(sys.argv[1:])
