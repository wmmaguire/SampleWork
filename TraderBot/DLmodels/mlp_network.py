# keras utilities
from keras.models import Sequential, model_from_json
from keras.callbacks import EarlyStopping
from keras.layers import Dense, Activation, Dropout
from tensorflow.python.client import device_lib
import json
import h5py
import numpy as np
import progressbar
bar_widgets = [
    'Training: ', progressbar.Percentage(), ' ', progressbar.Bar(marker="-", left="[", right="]"),
    ' ', progressbar.ETA()
]
callbacks = [EarlyStopping(monitor='loss', patience=2, verbose=0)]


class mlp_network():
    """
        Class to design, train and test a lstm network
    """
    filepath = ''
    val_data = None
    val_split = 0
    val_loss = None
    val_acc = None
    acc = []
    loss = []

    def __init__(self, X, y, model=None, batch_size=1, nb_epoch=300, step_size=1,
                 neurons=[60], stacks=1, val_split=0.0, val_data=None, classification=False, opt='rmsprop'):
        if len(neurons) is not stacks:
            print("Error: length of neurons must be equal to number of stacks")
            return
        self.batch_size = batch_size
        self.nepoch = nb_epoch
        self.neurons = neurons
        self.stacks = stacks
        self.step_size = step_size
        self.classiication = classification
        self.optimizer = opt
        # reshape X to (nSamples,timestep,features size), y is (nSamples, output)
        self.set_trainData(X, y)
        # Set validation set --> set self.val_loss to empty np array if needed
        self.set_valSplit(val_split)
        self.set_valData(val_data)
        # configuring model
        if not model:
            self.prepModel(classification)
        else:
            self.setModel()

    def set_valSplit(self, val_split):
        """
            set parameter to split training data into validation set:
                - input [val_split]: must be greater than 0 and less than 0.5
                - All X training data is reshaped into --> (nSamples,Timestep,Feature dimension)
        """
        if val_split >= 0 and val_split < 0.5:
            print("Setting validation split to ", val_split)
            self.val_split = val_split
        return

    def set_valData(self, val_data):
        """
            set parameter to test on validation data:
                - input [val_data]: must be list of [0] x data and [1] y data with matching nSamples
                - All X training data is reshaped into --> (nSamples,Timestep,Feature dimension)
        """
        if val_data:
            print("Setting validation Data with shape ", val_data[0].shape, val_data[1].shape)
            self.val_data = val_data
        return

    def set_trainData(self, X, y):
        """
            set training data
        """
        self.X = X
        self.y = y
        return

    # set file path
    def setFilePath(self, fpath):
        self.filepath = fpath
        return

        # set model
    def setModel(self, model):
        self.model = model
        return

        # Save model
    def saveModel(self, fname=""):
        filepath = self.filepath + fname
        if self.model:
            # serialize model to JSON
            model_json = self.model.to_json()
            with open(filepath + '.json', "w") as json_file:
                json_file.write(model_json)
            # serialize weights to HDF5
            self.model.save_weights(filepath + ".h5", overwrite=True)
            print("Saved model to " + filepath)
        return

    def prepModel(self, classification=False):
        """
        Method to compile a new lstm model based on user configurations
        """
        input_shape = (self.batch_size, self.X.shape[1], self.X.shape[2])
        # Structure model
        model = Sequential()
        # Add layers
        for stack in range(0, self.stacks):
            print("Adding MLP layer #%d,nodes %d" % (stack + 1,self.neurons))
            dense_layer = Dense(self.neurons, activation = 'tanh' )
            model.add(dense_layer)
            model.add(Dropout(0.5))
        # set output
        if classification:
            print("Compiling classification Model")
            model.add(Dense(self.y.shape[1], activation='softmax'))
            model.compile(loss='categorical_crossentropy', optimizer=self.optimizer, metrics=['accuracy'])
        else:
            print("Compiling regression Model")
            model.add(Dense(self.y.shape[1]))
            model.compile(loss='mse', optimizer=self.optimizer, metrics=['mape', 'mae'])
        self.model = model
        return model

    def fit_lstm(self):
        """
            Online training of training data
            --> log training loss and validation loss (if validation split or validation data provided)
        """
        if not self.model:
            print("Model not set.  Need to load exiting model or prep new model")
            return
        # Unpack data
        X = self.X
        y = self.y
        nepochs = self.nepoch
        batch_size = self.batch_size  # 1 for online training
        val_data = self.val_data
        val_split = self.val_split
        # set val_loss array if needed
        if val_data or val_split > 0:
            self.val_loss = []  # set val_loss instance
            self.val_acc = []  # set val_acc instance
        else:
            self.val_loss = None
            self.val_acc = None
        # To visualize progress
        bar = progressbar.ProgressBar(widget=bar_widgets)
        # Train
        history = self.model.fit(X, y, epochs=nepochs, batch_size=batch_size,
                                validation_split=val_split, validation_data=val_data,
                                verbose=0, shuffle=False, callbacks=callbacks)
        # log epoch loss values
        if self.val_loss is not None:
            self.val_loss = history.history['val_loss']
            if self.classiication:
                self.val_acc = history.history['val_acc']
        if self.classiication:
                self.acc = history.history['acc']
            self.loss = history.history['loss']
        return

    def forecast_MLP(self, X, batch_size=1):
        """
            method to forecast yhat given X using trained model
            *All X training data in--> (nSamples,Feature dimension)
        """
        if not self.model:
            print("Model not set.  Need to load exiting model or prep new model")
            return None
        yhat = self.model.predict(X, batch_size=batch_size)
        return yhat

    # evaluate model
    def evaluate_MLP(self, X, y):
        """
            method to evaluate trained model
        """
        if not self.model:
            print("Model not set.  Need to load exiting model or prep new model")
            return None
        return self.model.evaluate(X, y, batch_size=1)

    def walkForward(self, scaler, data_scaled, start=0):
        """
            method to conduct walkforward forecasting
        """
        if not self.model:
            print("Model not set.  Need to load exiting model or prep new model")
            return None
        # unpack test data
        x_scaled, y_scaled = data_scaled
        nySamples = y_scaled.shape[0]
        nxSamples = x_scaled.shape[0]

        # create arrays
        predictions = np.zeros(x_scaled.shape)
        err_array = np.zeros(nySamples)
        expected = np.zeros(y_scaled.shape)
        # walk through model
        for i in range(nySamples):
            # make one-step forecast
            X, y = x_scaled[i, :], y_scaled[i]
            yhat = self.forecast_lstm(X)[0]
            # re-invert scaling
            yhat = scaler.inverse_transform(yhat.reshape(-1, 1))[0]
            yactual = scaler.inverse_transform(y.reshape(-1, 1))[0]
            # find actual value and error
            rms_err = np.mean(np.sqrt(np.power((yhat - yactual), 2)))
            # store forecast
            err_array[i] = rms_err
            expected[i, :] = yactual
            predictions[i, :] = yhat
            if (i % int(nySamples / 10)) == 0:
                print('Minute=%d, Predicted=%f, Expected=%f' % (i + 1, yhat[-1], yactual[-1]))
        print('Minute=%d, Predicted=%f, Expected=%f' % (i + 1, yhat[-1], yactual[-1]))
        print("avg RMS: %.3f\n" % (np.mean(err_array)))
        # walk through rest of ata-set
        for j in range(nySamples, nxSamples):
            # make one-step forecast
            X = x_scaled[j, :]
            yhat = forecast_lstm(X)
            # re-invert scaling
            yhat = scaler.inverse_transform(yhat.reshape(-1, 1))[0]
            if (j == nxSamples - 1) or (j == nySamples):
                print('Future predictions: Minute=%d, Predicted=%f' % (j + 1, yhat[-1]))
            # store forecast
            predictions[j, :] = yhat
        # return results
        return expected, predictions, err_array
