import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import lyricsgenius
import pandas as pd
import json
import logging
import warnings
import requests
import six
import urllib3
import pymongo
from spotipy.exceptions import SpotifyException
from lyric_analysis import generate_wordcloud

__all__ = ["Spotify", "SpotifyException"]
logger = logging.getLogger(__name__)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="3277aa263a2444499975a8b48d2b9535",
                                                           client_secret="5a1f962128874070a4261c4898ff0d8e"))

genius_token = '723ukdudVE-FjrsmP8udKSTdYBSAEkAazEkqJ8zBmDGEPpLoLGbK3OZT2rC9UbQA'
genius = lyricsgenius.Genius(genius_token)
genius.timeout = 15

client = pymongo.MongoClient("mongodb+srv://testUser:bigData@cluster0.xn34j.mongodb.net")
db = client["MusicDataset"]
songInfo = db["songInfo"]
album_info = db["album_info"]


def get_artist_id(artist_name):
    id_count = {}
    results = sp.search(q=artist_name, limit=50)
    for idx, track in enumerate(results['tracks']['items']):
        for id, info in enumerate(track['album']['artists']):
            artist_id = info['id']
            if artist_id not in id_count:
                id_count[artist_id] = 1
            else:
                id_count[artist_id] += 1
    id_count = sorted(id_count, key=lambda x: (-id_count[x]))
    return id_count[0]


def get_artist_album(artist_name):
    # get albums of artist
    artist_id = get_artist_id(artist_name)
    albums = []
    results = sp.artist_albums(artist_id, album_type='album')
    albums.extend(results['items'])
    seen = set()  # to avoid duplicates
    albums.sort(key=lambda album: album['name'].lower())

    # add albums to mongodb
    for album in albums:
        name = album['name']
        # enters only if this album has not been entered before
        if name not in seen:
            seen.add(name)
            info = {
                "name" : name,
                "artist": artist_name, 
                "year" : album['release_date'], 
                "artist url" : album['artists'][0]['external_urls']['spotify'],
                "album url" : album['external_urls']['spotify'],
                "album cover url": album['images'][0]['url'],
                # base64 string gets added in lyric_analysis.py
                "base64 cover": ''
                }
            # mongodb add line
            album_info.insert_one(info)
            logger.info('ALBUM: %s', name)
    return seen


# Input:  album name (from get_artist_album)
#         artist_name (from artists.csv)
# Output: list of all songs in album where each song
#         is a dict containing: (title, lyrics, artist, album)
def get_album_songs(album_name,artist_name):
    try:
        album = genius.search_album(album_name, artist_name)
    except:
        return None
    if album == None:
        return None
    songs = []
    for i,song in enumerate(album.tracks):
        # get title
        title = album.tracks[i].song.title

        # get lyrics
        lyrics = album.tracks[i].song.lyrics
        lyrics = lyrics.split('\n')
        lyrics = " ".join(lyrics)
        if lyrics == "":
            continue

        # get artist
        artist = song.song.artist
        # get album
        album_title = album_name

        song = {
            "title" : title,
            "lyrics" : lyrics,
            "artist" : artist,
            "album" : album_title,
        }
        
        songs.append(song)
    return songs