from ncf_keras import GMF, MLP, NeuMF
from keras.callbacks import EarlyStopping
from keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
from scipy import sparse
import joblib

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class ncf():
    def __init__(self,
                 matrix_path='model_input.gz',
                 num_negatives=4):
        self.matrix_path = matrix_path
        self.num_negatives = num_negatives

        early_stop = EarlyStopping(monitor='val_loss',
                                   patience=3,
                                   restore_best_weights=True)
        self.callbacks = [early_stop]

    def load(self):
        print('Loading data')
        self.sparse_mat = joblib.load(self.matrix_path)
        self.get_train_data()

    def get_train_data(self):
        print('Building train matrices')
        self.train_mat, self.test_mat = train_test_split(
            self.sparse_mat, test_size=0.15)
        self.train_mat = sparse.dok_matrix(self.train_mat)
        self.test_mat = sparse.dok_matrix(self.test_mat)

        self.user_train, self.item_train, self.label_train = NeuMF.get_train_instances(
            self.train_mat, num_negatives=self.num_negatives)
        self.num_users_train, self.num_items_train = self.train_mat.shape

    def get_models(self):
        print('Getting models:')
        print(' - GMF')
        self.get_gmf()
        print(' - MLP')
        self.get_mlp()
        print(' - NeuMF')
        self.get_neumf()

    def get_gmf(self):
        num_factors = 8
        regs = [0, 0]

        lr = 0.001
        opt = Adam(lr=lr)

        self.gmf_model = GMF.get_model(self.num_users_train,
                                       self.num_items_train,
                                       num_factors,
                                       regs)
        self.gmf_model.compile(optimizer=opt,
                               loss='binary_crossentropy',
                               metrics=['acc'])

    def get_mlp(self):
        layers = [64, 32, 16, 8]
        reg_layers = [0, 0, 0, 0]

        lr = 0.001

        opt = Adam(lr=lr)

        self.mlp_model = MLP.get_model(self.num_users_train,
                                       self.num_items_train,
                                       layers,
                                       reg_layers)
        self.mlp_model.compile(
            optimizer=opt, loss='binary_crossentropy', metrics=['acc'])

    def get_neumf(self):
        layers = [64, 32, 16, 8]
        mf_dim = 8
        reg_layers = [0, 0, 0, 0]
        reg_mf = 0

        lr = 0.001
        opt = Adam(lr=lr)

        self.neumf_model = NeuMF.get_model(self.num_users_train,
                                           self.num_items_train,
                                           mf_dim, layers,
                                           reg_layers,
                                           reg_mf)
        self.neumf_model = NeuMF.load_pretrain_model(self.neumf_model,
                                                     self.gmf_model,
                                                     self.mlp_model,
                                                     len(layers))

        self.neumf_model.compile(
            optimizer=opt, loss='binary_crossentropy', metrics=['acc'])

    def summary(self):
        print('\n\nGMF MODEL SUMMARY')
        self.gmf_model.summary()
        print('\n\nMLP MODEL SUMMARY')
        self.mlp_model.summary()
        print('\n\nNEUMF MODEL SUMMARY')
        self.neumf_model.summary()

    def train(self):
        print('Training Models:')
        print(' - GMF')
        self.train_gmf()
        print(' - MLP')
        self.train_mlp()
        print(' - NeuMF')
        self.train_neumf()

    def train_gmf(self):
        batch_size = 256
        epochs = 20
        hist = self.gmf_model.fit([np.array(self.user_train),
                                   np.array(self.item_train)],
                                  np.array(self.label_train),
                                  batch_size=batch_size,
                                  epochs=epochs,
                                  callbacks=self.callbacks,
                                  validation_split=0.1,
                                  verbose=1,
                                  shuffle=True)
        self.gmf_model.save('./gmf_model.h5')

    def train_mlp(self):
        batch_size = 256
        epochs = 20
        hist = self.mlp_model.fit([np.array(self.user_train),
                                   np.array(self.item_train)],
                                  np.array(self.label_train),
                                  batch_size=batch_size,
                                  epochs=epochs,
                                  callbacks=self.callbacks,
                                  validation_split=0.1,
                                  verbose=1,
                                  shuffle=True)
        self.mlp_model.save('./mlp_model.h5')

    def train_neumf(self):
        batch_size = 256
        epochs = 20
        hist = self.neumf_model.fit([np.array(self.user_train),
                                     np.array(self.item_train)],
                                    np.array(self.label_train),
                                    batch_size=batch_size,
                                    epochs=epochs,
                                    callbacks=self.callbacks,
                                    validation_split=0.1,
                                    verbose=1,
                                    shuffle=True)
        self.neumf_model.save('./neumf_model.h5')
