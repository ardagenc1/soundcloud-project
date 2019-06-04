import soundcloud

# create client object with app credentials
client = soundcloud.Client(client_id='ifoUhYX2sDPbwwgaMnEYpMUXFBBWMQ3l')

page_size = 50

## print a track title
#track = client.get('/tracks/30709985')
#print(track.title)


## tracks = client.get('/tracks', genre = 'Techno', order='plays', limit = page_size, linked_partitioning=1)

#for count,song in enumerate(tracks):
#	print(count)
#	print(song.title)
	#if (count == 50):
	#	break;

# print(tracks.next_href)

# for count,song in enumerate(tracks.collection):
# 	print(count)
# 	print(song.title)


#Followers = client.get('/me/followings/3207')
#print(Followers)

# print users I follow
followings = client.get('users/300870231/followings', order = 'followers_count', limit = page_size, linked_partitioning=1)
followings_sorted = sorted(followings.collection, key=lambda x: x.followers_count, reverse=True)

for count,following in enumerate(followings_sorted):
	print(count)
	print(following.username)
	print("User %s has %d followers" % (following.username, following.followers_count))

# print my followers
followers = client.get('users/300870231/followers', limit = page_size, linked_partitioning=1)
followers_sorted = sorted(followers.collection, key=lambda x: x.followers_count, reverse=True)

for count,follower in enumerate(followers_sorted):
	print(count)
	print(follower.username)
	print("User %s has %d followers" % (follower.username, follower.followers_count))


# find tracks that a user has liked given user id.
favorites = client.get('users/300870231/favorites', limit = page_size, linked_partitioning=1)
link = favorites.next_href
client.get(link)
favorites_sorted = sorted(favorites.collection, key=lambda x: x.favoritings_count, reverse=True)

#given userID, return a list of songs that the user has liked sorted by number of total likes
userID = '300870231'

def getLikes(userID):
    favorites = client.get('users/' + userID + '/favorites', limit = page_size, linked_partitioning=1)
    printFavorites(favorites)
    try:
        while (favorites.next_href):
            favorites = client.get(favorites.next_href)
            printFavorites(favorites)
    except AttributeError:
        return
        

def printFavorites(favs):
    favs_sorted = sorted(favs.collection, key=lambda x: x.favoritings_count, reverse=True)
    for count, song in enumerate(favs_sorted):
        	print(count)
        	print("Track name: %s" %song.title)
        	print("Artist: %s" %song.user_id)
        	print("Track has been liked %d times" %song.favoritings_count)   
 



fav2_sorted = sorted(fav2.collection, key=lambda x: x.favoritings_count, reverse=True)


for count, song in enumerate(fav2_sorted):
	print(count)
	print("Track name: %s" %song.title)
	print("Artist: %s" %song.user_id)
	print("Track has been liked %d times" %song.favoritings_count)


# STRATEGY

# create a list of all user ids of the artists we want to include in the graph

# walk through the list of user ids, creating a list for each user containing their followers, followings, likes

# each user object should have the following fields: userid***, follower_count, following_count, maybe other things?


# IDEAS

# pull a bunch of songs, put them on a list, and extract artist user ids iterating through the list of songs using resolve.

# iterate through user ids, extract followers, followings, and likes of each user, store their ids. 

# study the follow/like relationship and try to predict links that will form (read the papers on graphs)

# try to work with IDs because they are unique, we can export other information later from the id, walking through the lists

# try using CVS file to store data


# QUESIONS

# How should we decide what subset of users we will work with?

# How will we ignore the users that aren't in the subset?

# How will we model the network as a graph?

# Which algorithms should we use to analyze the relationships and make predictions?















