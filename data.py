import soundcloud
import collections
import numpy as np
import pandas as pd
import joblib
from pdb import set_trace
import os
from scipy import sparse


class get_data():
    def __init__(self,
                 user_id=300870231,
                 depth=2,
                 client_id='ItE8O04ja93Qeo9H0TzvR6T3097EY02J',
                 page_size=200,
                 artist_threshold=3.0):

        self.userID = user_id
        self.client_id = client_id
        self.client = soundcloud.Client(client_id=self.client_id)

        self.page_size = page_size
        self.maxUserCalls = int(1000 / self.page_size)
        self.maxTrackCalls = int(2000 / self.page_size)

        self.artist_threshold = artist_threshold
        self.depth = depth

        self.user_fields = ["username", "track_count", "followers_count",
                            "followings_count", "public_favorites_count"]
        self.track_fields = ["id", "title", "track_type", "genre", "user"]

        self.cache_counter = 0

        self.users = {}
        self.tracks = {}
        self.user_tracks = []
        self.stack = []

        self.getUser(self.userID)

        self.stack.append({'type': 0, 'id': self.userID, 'depth': self.depth})

    def collect(self):
        if os.path.isfile('./users.gz'):
            self.load_cache()
        while self.stack:
            self.print_status()
            buf = self.stack.pop()
            if buf['depth'] == 0:
                continue
            else:
                if buf['type'] == 0:
                    self.getUserLikes(buf['id'], buf['depth'] - 1)
                    if self.isArtist(buf['id']):
                        self.getUserFollow(buf['id'],
                                           'followers',
                                           buf['depth'])
                        self.getArtistTracks(buf['id'], buf['depth'])
                    else:
                        self.getUserFollow(buf['id'],
                                           'followings',
                                           buf['depth'])
                else:
                    self.getTrackFavoriters(buf['id'], buf['depth'])
            self.cache_counter += 1
            if self.cache_counter == 100:
                self.save_cache()
                self.cache_counter = 0

    def getUser(self, userID):
        user = self.client.get(f'/users/{userID}').fields()
        self.users[user['id']] = dict((k, user[k]) for k in self.user_fields)

    def getUserLikes(self, userID, depth):
        try:
            user_tracks_res = self.client.get(f"users/{userID}/favorites",
                                              limit=self.page_size,
                                              linked_partitioning=1).fields()
            self.processUserTrackResults(
                userID, user_tracks_res['collection'], depth)
            try:
                for i in range(self.maxTrackCalls):
                    if user_tracks_res['next_href']:
                        break
                    user_tracks_res = self.client.get(
                        user_tracks_res['next_href']).fields()
                    self.processUserTrackResults(
                        userID, user_tracks_res['collection'], depth)
            except KeyError:
                return
        except Exception as e:
            return

    def processUserTrackResults(self, userID, results, depth):
        for track in results:
            track_id = track["id"]
            self.user_tracks.append([userID, track_id])
            if not track_id in self.tracks:
                self.tracks[track_id] = dict(
                    (k, track[k]) for k in self.track_fields)
                self.stack.append({'type': 1, 'id': track_id, 'depth': depth})

    def isArtist(self, userID):
        if self.users[userID]['track_count'] == 0:
            return False
        else:
            if self.users[userID]['followers_count'] / (self.users[userID]['followings_count'] + 1) > self.artist_threshold:
                if self.users[userID]['followers_count'] > 1000:
                    return True
            return False

    def getUserFollow(self, userID, endNode, depth):
        try:
            follow = self.client.get(f"users/{userID}/{endNode}",
                                     limit=self.page_size,
                                     linked_partitioning=1).fields()
            self.processUserResults(follow['collection'], depth)
            try:
                for i in range(self.maxUserCalls):
                    if follow['next_href']:
                        break
                    follow = self.client.get(follow['next_href']).fields()
                    self.processUserResults(follow['collection'], depth)
            except AttributeError:
                return

        except Exception as e:
            return

    def processUserResults(self, results, depth):
        for user in results:
            user_id = user["id"]
            if not user_id in self.users:
                self.users[user_id] = dict((k, user[k])
                                           for k in self.user_fields)
                self.stack.append({'type': 0, 'id': user_id, 'depth': depth})

    def getArtistTracks(self, userID, depth):
        try:
            user_tracks_res = self.client.get(f"users/{userID}/tracks",
                                              limit=self.page_size,
                                              linked_partitioning=1).fields()
            self.processUserTrackResults(
                userID, user_tracks_res['collection'], depth)
            try:
                for i in range(self.maxTrackCalls):
                    if user_tracks_res['next_href']:
                        break
                    user_tracks_res = self.client.get(
                        user_tracks_res['next_href']).fields()
                    self.processUserTrackResults(
                        userID, user_tracks_res['collection'], depth)
            except KeyError:
                return
        except Exception as e:
            return

    def getTrackFavoriters(self, trackID, depth):
        try:
            track_likers = self.client.get(f"tracks/{trackID}/favoriters",
                                           limit=self.page_size,
                                           linked_partitioning=1).fields()
            self.processUserResults(track_likers['collection'], depth)
            try:
                for i in range(self.maxTrackCalls):
                    if track_likers['next_href']:
                        break
                    track_likers = self.client.get(
                        track_likers['next_href']).fields()
                    self.processUserResults(track_likers['collection'], depth)
            except KeyError:
                return
        except Exception as e:
            return

    def print_status(self):
        print_str = f"Stack: {len(self.stack)}   "
        print_str += f"Users: {len(self.users)}   "
        print_str += f"Tracks: {len(self.tracks)}   "
        print_str += f"Hits: {len(self.user_tracks)}   "
        print_str += f"Cache in: {100-self.cache_counter}   "
        flush_str = ' '.rjust(len(print_str), ' ')
        print(flush_str, end='\r')
        print(print_str, end='\r')

    def get_model_input(self):
        self.load_cache(all=False)
        print('Building pivot table')
        y = np.array([np.array(xi) for xi in self.user_tracks])

        rows, r_pos = np.unique(y[:, 0], return_inverse=True)
        cols, c_pos = np.unique(y[:, 1], return_inverse=True)

        pivot_table = np.zeros((len(rows), len(cols)))
        pivot_table[r_pos, c_pos] = 1
        print('Converting pivot table to sparse')
        mat = sparse.dok_matrix(pivot_table)
        joblib.dump(mat, 'model_input.gz')
        return

        # print('Building df')
        # df = pd.DataFrame(data=y, columns=["userID", "trackID"])
        # print('Converting df to sparse')
        # df = df.groupby(['userID', 'trackID']).size().unstack(fill_value=0)
        # joblib.dump(df, 'model_input.gz')

        # t = pd.get_dummies(df, columns=['trackID'], prefix='', prefix_sep='').groupby(
        #     ['userID']).sum()
        # t.to_csv('./data.csv')

    def save_cache(self):
        joblib.dump(self.users, 'users.gz')
        joblib.dump(self.tracks, 'tracks.gz')
        joblib.dump(self.user_tracks, 'user_tracks.gz')
        joblib.dump(self.stack, 'stack.gz')

    def load_cache(self, all=True):
        print('Loading cache:')
        if all:
            print(' - users.gz')
            self.users = joblib.load('users.gz')
            print(' - tracks.gz')
            self.tracks = joblib.load('tracks.gz')
            print(' - stack.gz')
            self.stack = joblib.load('stack.gz')
        print(' - user_tracks.gz')
        self.user_tracks = joblib.load('user_tracks.gz')
