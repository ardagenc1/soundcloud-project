import soundcloud
import collections


userID = 300870231


client = soundcloud.Client(client_id='ifoUhYX2sDPbwwgaMnEYpMUXFBBWMQ3l')

page_size = 200
maxUserCalls = 1000 / page_size
maxTrackCalls = 3000 / page_size
artist_threshold = 3.0
depth = 2


users = {}
tracks = {}

user_tracks = [] 

user_fields = ["username", "track_count", "followers_count", "followings_count","public_favorites_count"] 
track_fields = ["id","title","track_type", "genre", "user"]


stack = []
Entry = collections.namedtuple('Entry', 'Type Id Depth')

  

def gatherData(userID,depth):
    global stack
    getUser(userID)
    ent = Entry(Type=0, Id=userID, Depth=depth)
    stack.append(ent)
    while stack:
        buf = stack.pop()
        if buf.Depth == 0:
            continue
        else:
            if buf.Type == 0:
                getUserLikes(buf.Id, buf.Depth)
                if isArtist(buf.Id):
                    getUserFollow(buf.Id, 'followers', buf.Depth)
                    getArtistTracks(buf.Id, buf.Depth)
                else:
                    getUserFollow(buf.Id, 'followings', buf.Depth)
            else:
                getTrackFavoriters(buf.Id, buf.Depth - 1)
                    
                

def getUser(userID):
    global users
    user = client.get('/users/' + str(userID)).fields()
    users[user['id']] = dict((k, user[k]) for k in user_fields)
    
    
    
def getUserFollow(userID, endNode, depth):
    try:
        follow = client.get("users/" + str(userID) + "/" + endNode, limit = page_size, linked_partitioning = 1).fields()
        processUserResults(follow['collection'], depth)
        counter = 0
        try:
            while(follow['next_href'] and counter < maxUserCalls):
                follow = client.get(follow['next_href']).fields()
                processUserResults(follow['collection'], depth)
                counter = counter + 1
        except AttributeError:
            return
    
    except Exception:
        return


def getUserLikes(userID, depth):
    try:
        user_tracks_res = client.get("users/" + str(userID) + "/favorites", limit = page_size, linked_partitioning = 1).fields()
        processUserTrackResults(userID, user_tracks_res['collection'], depth)
        counter = 0
        try:
            while(user_tracks_res['next_href'] and counter < maxTrackCalls):
                user_tracks_res = client.get(user_tracks_res['next_href']).fields()
                processUserTrackResults(user_tracks_res['collection'], depth)
                counter = counter + 1
        except KeyError:
            return   
    except Exception:
        return


def getArtistTracks(userID, depth):
    try:
        user_tracks_res = client.get("users/" + str(userID) + "/tracks", limit = page_size, linked_partitioning = 1).fields()
        processUserTrackResults(userID, user_tracks_res['collection'], depth)
        counter = 0
        try:
            while(user_tracks_res['next_href'] and counter < maxTrackCalls):
                user_tracks_res = client.get(user_tracks_res['next_href']).fields()
                processUserTrackResults(user_tracks_res['collection'], depth)
                counter = counter + 1
        except KeyError:
            return
    except Exception:
        return


def getTrackFavoriters(trackID, depth):
    try:
        track_likers = client.get("tracks/" + str(trackID) + "/favoriters", limit = page_size, linked_partitioning = 1).fields()
        processUserResults(track_likers['collection'], depth)
        counter = 0
        try:
            while(track_likers['next_href'] and counter < maxTrackCalls):
                track_likers = client.get(track_likers['next_href']).fields()
                processUserResults(track_likers['collection'], depth)
                counter = counter + 1
        except KeyError:
            return
    except Exception:
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




