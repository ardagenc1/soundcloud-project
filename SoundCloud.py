import soundcloud

# create client object with app credentials
client = soundcloud.Client(client_id='ifoUhYX2sDPbwwgaMnEYpMUXFBBWMQ3l')

page_size = 200

# print a track title
track = client.get('/tracks/30709985')
print(track.title)


# tracks = client.get('/tracks', genre = 'Techno', order='plays', limit = page_size, linked_partitioning=1)

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

# print my fucking followers
followings = client.get('users/3207/followings')
for count,following in enumerate(followings.collection):
	print(count)
	print(following.id)