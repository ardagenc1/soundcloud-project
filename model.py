from ncf_keras import GMF, MLP, NeuMF
from keras.callbacks import EarlyStopping
from keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
from scipy import sparse
import joblib
from pdb import set_trace
from keras.models import load_model
import os
import random
from tqdm.auto import tqdm
import matplotlib.pyplot as plt


class ncf():
    def __init__(self,
                 input_path='./collection/user_tracks.gz',
                 num_negatives=4):
        self.input_path = input_path
        self.num_negatives = num_negatives

        early_stop = EarlyStopping(monitor='val_loss',
                                   patience=4,
                                   restore_best_weights=True)
        self.callbacks = [early_stop]

        for dir in ['weights', 'collection', 'plots']:
            if not os.path.exists(dir):
                os.makedirs(dir)

        self.load()

    def load(self):
        print('Loading data')
        self.get_model_input()
        self.get_train_data()

    def get_model_input(self):
        self.user_tracks = joblib.load(self.input_path)
        print('Building model input')

        y = np.array([np.array(xi) for xi in self.user_tracks])
        self.tracks_df = pd.DataFrame({'user': y[:, 0], 'track': y[:, 1]})

        rows, r_pos = np.unique(y[:, 0], return_inverse=True)
        cols, c_pos = np.unique(y[:, 1], return_inverse=True)

        self.user_dict = {v: i for i, v in enumerate(rows)}
        self.track_dict = {v: i for i, v in enumerate(cols)}

        self.sparse_mat = sparse.dok_matrix((len(rows), len(cols)), dtype=int)
        self.sparse_mat[r_pos, c_pos] = 1

    def get_train_data(self):
        print('Building train matrices')
        self.user_train, self.item_train, self.label_train = NeuMF.get_train_instances(
            self.sparse_mat, num_negatives=self.num_negatives)
        self.num_users_train, self.num_items_train = self.sparse_mat.shape

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

    def hit_ratio(self, model='neumf', n=10):
        if model == 'gmf':
            model = self.gmf_model
        if model == 'mlp':
            model = self.mlp_model
        else:
            model = self.neumf_model

        users = list(self.user_dict)
        num_test_users = int(len(users) * .15)
        test_users = random.sample(users, num_test_users)

        hits = 0
        for user in tqdm(test_users):
            hits += self.test_user_hit_ratio(user, model, n)

        ratio = hits / len(test_users)
        print(f'\nHR @ {n}: {ratio}')
        return ratio

    def test_user_hit_ratio(self, user=163190, model=None, n=10):
        user_mat = self.get_user_mat(user)
        _, nonzero = user_mat.nonzero()

        track = np.random.choice(nonzero, 1)[0]

        user_mat = sparse.dok_matrix(1 - user_mat.toarray())
        inputs, items, _ = NeuMF.get_train_instances(user_mat, 0)

        inputs_sample, items_sample = zip(
            *random.sample(list(zip(inputs, items)), 99))
        inputs_sample = list(inputs_sample)
        items_sample = list(items_sample)

        inputs_sample.append(0)
        items_sample.append(track)

        preds = model.predict_on_batch([np.array(inputs_sample),
                                        np.array(items_sample)])[:, 0]

        _, nonzero = user_mat.nonzero()

        df = pd.DataFrame({'track': items_sample, 'pred': preds})
        df = df.sort_values('pred', ascending=False)
        df = df.reset_index(drop=True)

        if df[df.track == track].index[0] <= n:
            return 1
        return 0

    def get_user_results(self, user=163190):
        user_mat = self.get_user_mat(user)
        user_mat = sparse.dok_matrix(1 - user_mat.toarray())
        inputs, items, _ = NeuMF.get_train_instances(user_mat, 0)

        preds = self.neumf_model.predict_on_batch([np.array(inputs),
                                                   np.array(items)])[:, 0]

        _, nonzero = user_mat.nonzero()

        df = pd.DataFrame({'track': nonzero, 'pred': preds})
        df = df.sort_values('pred', ascending=False)
        df = df.reset_index(drop=True)
        return df

    def get_user_mat(self, user=163190):
        return self.sparse_mat[self.user_dict[user]]

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
        self.gmf_model.save('./weights/gmf_model.h5')
        self.get_log_graph(hist, 'gmf')

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
        self.mlp_model.save('./weights/mlp_model.h5')
        self.get_log_graph(hist, 'mlp')

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
        self.neumf_model.save('./weights/neumf_model.h5')
        self.get_log_graph(hist, 'neumf')

    def get_log_graph(self, hist, name):
        # Plot training & validation accuracy values
        plt.plot(hist.history['acc'])
        plt.plot(hist.history['val_acc'])
        plt.title(f'{name} accuracy')
        plt.ylabel('Accuracy')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Test'], loc='upper left')
        plt.savefig(f'./plots/{name}_acc.png')
        plt.clf()

        # Plot training & validation loss values
        plt.plot(hist.history['loss'])
        plt.plot(hist.history['val_loss'])
        plt.title(f'{name} loss')
        plt.ylabel('Loss')
        plt.xlabel('Epoch')
        plt.legend(['Train', 'Test'], loc='upper left')
        plt.savefig(f'./plots/{name}_loss.png')
        plt.clf()

    def load_models(self):
        self.gmf_model = load_model('./weights/gmf_model.h5')
        self.mlp_model = load_model('./weights/mlp_model.h5')
        self.neumf_model = load_model('./weights/neumf_model.h5')
