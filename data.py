import soundcloud
import collections
import numpy as np
import pandas as pd
import joblib
from pdb import set_trace
import logging
from tqdm.auto import tqdm
import os
import sys


class soundcloud_api():
    def __init__(self,
                 user_id=300870231,
                 client_id='ItE8O04ja93Qeo9H0TzvR6T3097EY02J',
                 page_size=200,
                 artist_threshold=3.0,
                 depth=2):

        self.userID = user_id
        self.client_id = client_id
        self.client = soundcloud.Client(client_id=self.client_id)

        self.page_size = page_size
        self.maxUserCalls = int(1000 / self.page_size)
        self.maxTrackCalls = int(2000 / self.page_size)

        self.artist_threshold = artist_threshold
        self.depth = depth

        self.user_counter = 0
        self.get_counter = 0

        self.users = {}
        self.tracks = {}

        self.user_tracks = []

        self.user_fields = ["username", "track_count", "followers_count",
                            "followings_count", "public_favorites_count"]
        self.track_fields = ["id", "title", "track_type", "genre", "user"]

        self.stack = []
        self.Entry = collections.namedtuple('Entry', 'Type Id Depth')

        self.getUser(self.userID)
        ent = self.Entry(Type=0, Id=self.userID, Depth=self.depth)
        self.stack.append(ent)

    def getUser(self, userID):
        user = self.client.get(f'/users/{userID}').fields()
        self.get_counter += 1
        self.users[user['id']] = dict((k, user[k]) for k in self.user_fields)

    def gatherData(self):
        write_counter = 0
        while self.stack:
            print_str = f"Stack: {len(self.stack)}   "
            print_str += f"Users: {len(self.users)}   "
            print_str += f"Tracks: {len(self.tracks)}   "
            print_str += f"Hits: {len(self.user_tracks)}   "
            print_str += f"Cache in: {100-write_counter}   "
            flush_str = ' '.rjust(len(print_str), ' ')
            print(flush_str, end='\r')
            print(print_str, end='\r')
            buf = self.stack.pop()
            if buf.Depth == 0:
                continue
            else:
                if buf.Type == 0:
                    self.getUserLikes(buf.Id, buf.Depth - 1)
                    if self.isArtist(buf.Id):
                        self.getUserFollow(buf.Id, 'followers', buf.Depth)
                        self.getArtistTracks(buf.Id, buf.Depth)
                    else:
                        self.getUserFollow(buf.Id, 'followings', buf.Depth)
                else:
                    self.getTrackFavoriters(buf.Id, buf.Depth)
            write_counter += 1
            if write_counter == 100:
                self.save_user_tracks()
                write_counter = 0

    def getUserLikes(self, userID, depth):
        try:
            self.user_counter += 1
            user_tracks_res = self.client.get(f"users/{userID}/favorites",
                                              limit=self.page_size,
                                              linked_partitioning=1).fields()
            self.get_counter += 1
            self.processUserTrackResults(
                userID, user_tracks_res['collection'], depth)
            try:
                for i in range(self.maxTrackCalls):
                    if user_tracks_res['next_href']:
                        break
                    user_tracks_res = self.client.get(
                        user_tracks_res['next_href']).fields()
                    self.get_counter += 1
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
                ent = self.Entry(Type=1, Id=track_id, Depth=depth)
                self.stack.append(ent)

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
            self.get_counter += 1
            self.processUserResults(follow['collection'], depth)
            try:
                for i in range(self.maxUserCalls):
                    if follow['next_href']:
                        break
                    follow = self.client.get(follow['next_href']).fields()
                    self.get_counter += 1
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
                ent = self.Entry(Type=0, Id=user_id, Depth=depth)
                self.stack.append(ent)

    def getArtistTracks(self, userID, depth):
        try:
            user_tracks_res = self.client.get(f"users/{userID}/tracks",
                                              limit=self.page_size,
                                              linked_partitioning=1).fields()
            self.get_counter += 1
            self.processUserTrackResults(
                userID, user_tracks_res['collection'], depth)
            try:
                for i in range(self.maxTrackCalls):
                    if user_tracks_res['next_href']:
                        break
                    user_tracks_res = self.client.get(
                        user_tracks_res['next_href']).fields()
                    self.get_counter += 1
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
            self.get_counter += 1
            self.processUserResults(track_likers['collection'], depth)
            try:
                for i in range(self.maxTrackCalls):
                    if track_likers['next_href']:
                        break
                    track_likers = self.client.get(
                        track_likers['next_href']).fields()
                    self.get_counter += 1
                    self.processUserResults(track_likers['collection'], depth)
            except KeyError:
                return
        except Exception as e:
            return

    def save_user_tracks(self):
        print('Saving df')
        y = np.array([np.array(xi) for xi in self.user_tracks])
        df = pd.DataFrame(data=y, columns=["userID", "trackID"])
        joblib.dump(df, 'tracks.gz')
        return
        # df.groupby(['user', 'product']).size().unstack(fill_value=0).to_csv('./data.csv')
        t = pd.get_dummies(df, columns=['trackID'], prefix='', prefix_sep='').groupby(
            ['userID']).sum()
        t.to_csv('./data.csv')


api = soundcloud_api(user_id=300870231,
                     depth=2)
api.gatherData()
