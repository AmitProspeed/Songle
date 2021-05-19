#following this tutorial: https://flask.palletsprojects.com/en/1.1.x/quickstart/
#                         https://medium.com/techcrush/how-to-render-html-file-in-flask-3fbfb16b47f6

from flask import Flask, render_template, request
from search import Search
from pymongo import MongoClient
from bson.objectid import ObjectId
import lyric_analysis as la

app = Flask(__name__)
# SESSION_TYPE = 'mongodb'
# app.config.from_object(__name__)
# Session(app)

#initialize MongDB connections
client = MongoClient("mongodb+srv://testUser:bigData@cluster0.xn34j.mongodb.net")
db = client["MusicDataset"]
songInfo = db["songInfo"]
album_info = db["album_info"]
songIndex = db["index"]

#create index on server start
searchObj = Search()
print("Loading Index...Please wait")
searchObj.createIndex()
print("Index loaded successfully")

# @app.route('/set/')
# def set():
    
#     return 'ok'

@app.route('/')
def render_home():
  return render_template('homepage.html')

# https://developer.mozilla.org/en-US/docs/Learn/Forms/Sending_and_retrieving_form_data
# https://pythonbasics.org/flask-http-methods/
# https://www.digitalocean.com/community/tutorials/processing-incoming-request-data-in-flask
@app.route('/search', methods = ['GET'])
def render_matches():
  searchBar = request.args.get('searchBar')
  allResults = searchObj.queryIndex(searchBar)     #array of song ids
  #print(allResults)
  if len(allResults) > 10:
    topResults = allResults[0:10]
  else:
    topResults = allResults

  matches = [] #matches should be an array of songs with the information in JSON format
  for song_id in topResults: 
    query = {'_id': ObjectId(song_id)}
    song = songInfo.find_one(query, {'title':1, 'artist':1})
    matches.append(song)
  #print(matches)

  ### FOR SENDING DATA TO HTML TO RENDER ON THE FLY ###
  # LOOK INTO JINJA2
  # https://stackoverflow.com/questions/51669102/how-to-pass-data-to-html-page-using-flask
  # https://pythonbasics.org/flask-template-data/
  return render_template('matches.html', matches=matches)


@app.route('/song', methods = ['GET'])
def render_song_page():

    # query for song info 
    song_id = request.args.get('songId')
    query = {'_id': ObjectId(song_id)}
    song = songInfo.find_one(query)

    #getting the album cover 
    query_album = {'name': song['album'], 'artist': song['artist']}
    album_links = album_info.find_one(query_album, {"album cover url":1, "album url":1, "name":1,"artist url":1})
    album_base64 = album_info.find_one(query_album, {"base64 cover":1})
    
    # embeded spotify album link
    album_url = album_links['album url']
    split = album_url.split('/')
    album_url = '/'.join(split[0:3]) +'/embed/'+ '/'.join(split[3:5])
    
    # embeded spotify artist link
    artist_url = album_links['artist url']
    split = artist_url.split('/')
    artist_url = '/'.join(split[0:3]) +'/embed/'+ '/'.join(split[3:5])

    # spotify links:
    spotify_urls = {
      'album url' : album_url,
      'artist url' : artist_url
    }
    # wordclouds. 
    wc = {
      'album wordcloud' : la.generate_wordcloud(song['album'],song['artist']).decode('utf-8'),
      'song wordcloud' : la.gen_wordcloud_one_song(album_links['album cover url'],song['lyrics']).decode('utf-8')
    }
    
    # sentiment analysis
    sa = la.calculate_sentiment(song['lyrics'])
    """ What does the return value mean?
    if sa == 1:
        sentiment = "positive"
    elif sa == 0:
        sentiment = "neutral"
    else:
        sentiment = "negative"
    """

    return render_template('song.html', song=song, wc=wc, sa=sa, album_links=album_links,spotify_urls=spotify_urls)

# this has something to do with refreshing the page. 
@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r
if __name__ == '__main__':
   app.run()