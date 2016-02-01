from __future__ import print_function
import numpy as np
import pandas as pd
np.random.seed(1337)  # for reproducibility

from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.normalization import BatchNormalization
from keras.layers.advanced_activations import Quorum
from keras.utils import np_utils
from keras import backend as K
from keras.optimizers import Adam

from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler


def load_data(path, train=True):
    df = pd.read_csv(path)
    X = df.values.copy()
    if train:
        np.random.shuffle(X)  # https://youtu.be/uyUXoap67N8
        X, labels = X[:, 1:-1].astype(np.float32), X[:, -1]
        return X, labels
    else:
        X, ids = X[:, 1:].astype(np.float32), X[:, 0].astype(str)
        return X, ids


def preprocess_data(X, scaler=None):
    if not scaler:
        scaler = StandardScaler()
        scaler.fit(X)
    X = scaler.transform(X)
    return X, scaler


def preprocess_labels(labels, encoder=None, categorical=True):
    if not encoder:
        encoder = LabelEncoder()
        encoder.fit(labels)
    y = encoder.transform(labels).astype(np.int32)
    if categorical:
        y = np_utils.to_categorical(y)
    return y, encoder


def make_submission(y_prob, ids, encoder, fname):
    with open(fname, 'w') as f:
        f.write('id,')
        f.write(','.join([str(i) for i in encoder.classes_]))
        f.write('\n')
        for i, probs in zip(ids, y_prob):
            probas = ','.join([i] + [str(p) for p in probs.tolist()])
            f.write(probas)
            f.write('\n')
    print('Wrote submission to file {}.'.format(fname))

def step(x, alpha=0):
    return K.switch(alpha, 0, 1)

print('Loading data...')
X, labels = load_data('train.csv', train=True)
X, scaler = preprocess_data(X)
y, encoder = preprocess_labels(labels)

X_test, ids = load_data('test.csv', train=False)
X_test, _ = preprocess_data(X_test, scaler)

nb_classes = y.shape[1]
print(nb_classes, 'classes')

dims = X.shape[1]
print(dims, 'dims')

print('Building model...')

model = Sequential()
model.add(Dense(512, input_shape=(dims,)))
model.add(Quorum([K.relu, step], trainable=False))
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Dense(512))
model.add(Quorum([K.relu, step], trainable=False))
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Dense(512))
model.add(Quorum([K.relu, step], trainable=False))
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Dense(nb_classes))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy', optimizer='adam')

print('Training model...')
model.fit(X, y, nb_epoch=20, batch_size=128, validation_split=0.15)

print('Generating submission...')
proba = model.predict_proba(X_test)
make_submission(proba, ids, encoder, fname='keras-otto.csv')
