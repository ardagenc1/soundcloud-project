import soundcloud
import collections
import numpy as np
import pandas as pd


userID = 300870231


client = soundcloud.Client(client_id='ItE8O04ja93Qeo9H0TzvR6T3097EY02J')

page_size = 200
maxUserCalls = 1000 / page_size
maxTrackCalls = 2000 / page_size
artist_threshold = 3.0
depth = 2

debug_counter = 0
user_counter = 0
get_counter = 0

users = {}
tracks = {}

user_tracks = []

user_fields = ["username", "track_count", "followers_count",
               "followings_count", "public_favorites_count"]
track_fields = ["id", "title", "track_type", "genre", "user"]


stack = []
Entry = collections.namedtuple('Entry', 'Type Id Depth')


def initialize(userID, depth):
    global stack
    getUser(userID)
    ent = Entry(Type=0, Id=userID, Depth=depth)
    stack.append(ent)


def gatherData():
    global stack
    global debug_counter
    global user_counter
    global get_counter
    write_counter = 0
    while stack:
        #print("getUserLikes counter is: {}".format(user_counter))
        #print("the debug counter is: {}".format(debug_counter))
        #print("API get counter is: {}".format(get_counter))
        if debug_counter == 5:
            # print("====================================================")
            # print("\n")
            #print("Stack  len: {}".format(len(stack)))
            #print("Users  len: {}".format(len(users)))
            #print("Tracks len: {}".format(len(tracks)))
            #print("user_tracks: {}".format(len(user_tracks)))
            # print("====================================================")
            debug_counter = 0
        buf = stack.pop()
        if buf.Depth == 0:
            debug_counter += 1
            continue
        else:
            if buf.Type == 0:
                getUserLikes(buf.Id, buf.Depth - 1)
                if isArtist(buf.Id):
                    getUserFollow(buf.Id, 'followers', buf.Depth)
                    getArtistTracks(buf.Id, buf.Depth)
                else:
                    getUserFollow(buf.Id, 'followings', buf.Depth)
            else:
                getTrackFavoriters(buf.Id, buf.Depth)
        debug_counter += 1
        write_counter += 1
        print(f'WRITE_COUNTER: {write_counter}')
        if write_counter == 100:
            save_user_tracks()
            write_counter = 0


def save_user_tracks():
    global user_tracks
    y = np.array([np.array(xi) for xi in user_tracks])
    df = pd.DataFrame(data=y, columns=["userID", "trackID"])
    t = pd.get_dummies(df, columns=['trackID'], prefix='', prefix_sep='').groupby(
        ['userID']).sum()
    t.to_csv('./data.csv')


def getUser(userID):
    global users
    global get_counter
    user = client.get('/users/' + str(userID)).fields()
    get_counter += 1
    users[user['id']] = dict((k, user[k]) for k in user_fields)


def getUserFollow(userID, endNode, depth):
    #print("getUserFollow", userID)
    try:
        global maxUserCalls
        global get_counter
        follow = client.get("users/" + str(userID) + "/" + endNode,
                            limit=page_size, linked_partitioning=1).fields()
        get_counter += 1
        processUserResults(follow['collection'], depth)
        counter = 0
        try:
            while(follow['next_href'] and counter < maxUserCalls):
                follow = client.get(follow['next_href']).fields()
                get_counter += 1
                processUserResults(follow['collection'], depth)
                counter = counter + 1
        except AttributeError:
            return

    except Exception as e:
        # print(e)
        return


def getUserLikes(userID, depth):
    #print("getUserLikes", userID)
    try:
        global maxTrackCalls
        global user_counter
        global get_counter
        user_counter += 1
        user_tracks_res = client.get(
            "users/" + str(userID) + "/favorites", limit=page_size, linked_partitioning=1).fields()
        get_counter += 1
        processUserTrackResults(userID, user_tracks_res['collection'], depth)
        counter = 0
        try:
            while(user_tracks_res['next_href'] and counter < maxTrackCalls):
                user_tracks_res = client.get(
                    user_tracks_res['next_href']).fields()
                get_counter += 1
                processUserTrackResults(
                    userID, user_tracks_res['collection'], depth)
                counter = counter + 1
        except KeyError:
            return
    except Exception as e:
        # print(e)
        return


def getArtistTracks(userID, depth):
    #print("getArtistTrackset", userID)
    try:
        global maxTrackCalls
        global get_counter
        user_tracks_res = client.get(
            "users/" + str(userID) + "/tracks", limit=page_size, linked_partitioning=1).fields()
        get_counter += 1
        processUserTrackResults(userID, user_tracks_res['collection'], depth)
        counter = 0
        try:
            while(user_tracks_res['next_href'] and counter < maxTrackCalls):
                user_tracks_res = client.get(
                    user_tracks_res['next_href']).fields()
                get_counter += 1
                processUserTrackResults(
                    userID, user_tracks_res['collection'], depth)
                counter = counter + 1
        except KeyError:
            return
    except Exception as e:
        # print(e)
        return


def getTrackFavoriters(trackID, depth):
    #print("getTrackFavoriters", trackID)
    try:
        global maxTrackCalls
        global get_counter
        track_likers = client.get(
            "tracks/" + str(trackID) + "/favoriters", limit=page_size, linked_partitioning=1).fields()
        get_counter += 1
        processUserResults(track_likers['collection'], depth)
        counter = 0
        try:
            while(track_likers['next_href'] and counter < maxTrackCalls):
                track_likers = client.get(track_likers['next_href']).fields()
                get_counter += 1
                processUserResults(track_likers['collection'], depth)
                counter = counter + 1
        except KeyError:
            return
    except Exception as e:
        # print(e)
        return


def processUserResults(results, depth):
    global stack
    global users
    for user in results:
        user_id = user["id"]
        if not user_id in users:
            users[user_id] = dict((k, user[k]) for k in user_fields)
            ent = Entry(Type=0, Id=user_id, Depth=depth)
            stack.append(ent)


def processUserTrackResults(userID, results, depth):
    global stack
    global tracks
    global user_tracks
    for track in results:
        track_id = track["id"]
        user_tracks.append([userID, track_id])
        if not track_id in tracks:
            tracks[track_id] = dict((k, track[k]) for k in track_fields)
            ent = Entry(Type=1, Id=track_id, Depth=depth)
            stack.append(ent)


def isArtist(userID):
    global users
    global artist_threshold
    if users[userID]['track_count'] == 0:
        return False
    else:
        if (users[userID]['followers_count'] / (users[userID]['followings_count'] + 1) > artist_threshold) and (users[userID]['followers_count'] > 1000):
            return True
        else:
            return False


if __name__ == "__main__":
    initialize(userID, depth)
    gatherData()
