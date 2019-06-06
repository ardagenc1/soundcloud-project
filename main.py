import soundcloud
import pandas as pd
import collections


userID = '300870231'


client = soundcloud.Client(client_id='ifoUhYX2sDPbwwgaMnEYpMUXFBBWMQ3l')

pageSize = 200


# tables:
#   Users: id, username, full_name, track_count, playlist_count, followers_count, followings_count, public_favorites_count, analyzed_flag
#   Tracks: id, 
#   UserTracks: userID, trackID
# dictionary:
#      
#   UserFollowers: key: userID, value: list of followers
#   UserFollowing: key: userID, value: list of following    



users_cols = ["id", "permalink", "username", "uri", "permalink_url", "avatar_url", "country",\
              "full_name", "city", "description", "discogs_name", "myspace_name", "website", \
              "website_title", "online", "track_count", "playlist_count", "followers_count",\
              "followings_count","public_favorites_count"]
users = pd.DataFrame(columns = users_cols)

tracks_cols = ["id", "created_at", "user_id", "duration", "commentable", "state", "sharing", "tag_list",\
               "permalink", "description", "streamable", "downloadable", "genre", "release", "purchase_url", \
               "label_id", "label_name", "isrc",
  "video_url",
  "track_type",
  "key_signature",
  "bpm",
  "title",
  "release_year",
  "release_month",
  "release_day",
  "original_format",
  "original_content_size",
  "license",
  "uri",
  "permalink_url",
  "artwork_url",
  "waveform_url",
  "user",
    "id",
    "permalink",
    "username",
    "uri"
    "permalink_url"
  "avatar_url"
  "stream_url"
  "download_url"
  "playback_count"
  "download_count"
  "favoritings_count"
  "comment_count"
  "attachments_uri"


stack = []
Entry = collections.namedtuple('Entry', 'Type Id Depth')



# main(userID) -> list of recommeded tracks
# Input : userID
# Output: recommended track ids

# getUser(userID) 
# stack: {type: user/track; id ; depth counter}
# push(user)
# while (stack not empty):   
#   buf = stack.pop
#   if buf.depth = 0
#        continue
#   else:
#       if buf.type == user: (0)
#           getUserTracks(userID)    
#           if isArtist(buf.id):
#               getUserFollowers(userID, buf.depth)    
#           else:
#               getUserFollowing(userID, buf.depth)
#       else if buf.type == track: (1)
#           getTrackFavoriters(trackID, buf.depth - 1)    





def getUser(iD):
    global users
    user = client.get('/users/' + iD).fields()
    user = pd.DataFrame.from_dict(user)
    users = pd.concat([users, user], ignore_index = True)
    
    
def getUserFollow(userID, endNode, depth):
    follow = client.get("users/" + userID + "/" + endNode, limit = page_size, linked_partitioning = 1).fields()
    result = pd.DataFrame.from_dict(follow['collection']).set_index('id')
    processFollowResults(result, depth)
    
    
    
    for favorite in favorites.collection:
    #create struct for favorite
    #push struct to stack
    try:
        while(favorites.next_href):
            favorites = client.get(favorites.next_href)
            # add curr part to pd Dataframe
            for favorite in favorites.collection:
                #create struct for favorite
                #push struct to stack
    except AttributeError:
    #return ?
    #return ?    



def processFollowResults(result, depth):   
    global stack
    global users         
    for index, user in result.iterrows():
        if not index in users.index:
            ent = Entry(Type=0, Id=index, Depth=depth)
            stack.append(ent)
            users = users.append(user, ignore_index = False)
        
    
    


# getUserTracks(userdID)
# getUserFollowers(userID)
# getUsersFollowing(userID)
# getTrackFavoriters(trackID)



# isArtist(userID) -> bool
# given a userID and attributes, determine if user is an "artist" (threshold on distribution of attributes like tracks published)
# ratio of indegree / outdegree


