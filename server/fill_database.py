import collect_songs as ab
import pymongo
import requests
import pandas as pd
import numpy as np
from lyric_analysis import generate_wordcloud


client = pymongo.MongoClient("mongodb+srv://testUser:bigData@cluster0.xn34j.mongodb.net")
db = client["MusicDataset"]
songInfo = db["songInfo"]

# read in artists csv
heading = ["name", "facebook", "twitter", "website", "genre", "mtv"]
df = pd.read_csv('Artists.csv', names = heading)
artist_name = df.values[:, :1].ravel()
# remove no name artists (these are present in artist.csv)
artist_name = [i for i in artist_name if i is not np.nan]
# remove leading and trailing whitespace
artist_name = np.char.strip(artist_name)

# get songs from artists in artist_name
for artist in artist_name[10:11]: # -> for trial run use this instead of running the whole artist list
#for name in artist_name:
    # finds albums from artist 
    albums = ab.get_artist_album(artist)
    if albums == None:
        break
    for album in albums:
        # finds songs from album, inserts into database
        album_songs = ab.get_album_songs(album,artist)
        if album_songs == None:
            continue
        # insert songs into database
        songInfo.insert_many(album_songs)
        wc = generate_wordcloud(album,artist)


