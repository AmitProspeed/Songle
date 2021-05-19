import io
import matplotlib
# uses non-GUI. Solves for running on server
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import re
plt.style.use('seaborn')
from pymongo import MongoClient
from wordcloud import WordCloud, STOPWORDS
import nltk
# nltk.download('stopwords')
# nltk.download('punkt')
# nltk.download('wordnet')
# nltk.download('averaged_perceptron_tagger')
from nltk.corpus import stopwords
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
from PIL import Image
import requests
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import base64
from io import BytesIO
from PIL import Image, ImageShow
import csv
import pandas as pd

client = MongoClient("mongodb+srv://testUser:bigData@cluster0.xn34j.mongodb.net")
db = client["MusicDataset"]
songInfo = db["songInfo"]
albumInfo = db["album_info"]

# used in text_process and generate_wordcloud
stop_words = set(stopwords.words('english'))


def text_preprocessing(text):
    text = re.sub(r'[^\w\s]', ' ', text)
    #tokenizer = word_tokenize()
    lemmatizer = WordNetLemmatizer()

    tokens = word_tokenize(text)
    lemmas = []
    for word in tokens:
        if word.isalpha() and not word in stop_words:
            word = word.lower()
            word = lemmatizer.lemmatize(word, pos='v')
            lemmas.append(word)
    tokens = lemmas
    while "" in tokens:
        tokens.remove("")
    while " " in tokens:
        tokens.remove(" ")
    while "\n" in tokens:
        tokens.remove("\n")
    while "\n\n" in tokens:
        tokens.remove("\n\n")
    return tokens

def generate_wordcloud(album,artist_name):
    # for encoding image to base64 MUST BE LOCAL VAR
    my_stringIObytes = io.BytesIO()
    # for lyric string manipulation
    common_words = ''

    # get album info from arguments. 
    query = {"name": album, "artist": artist_name}
    artist_album_info = albumInfo.find_one(query)
    
    #check if album encoding exists in album_info db
    # if encoding exists, return encoding, not generate new
    if artist_album_info["base64 cover"] != "":
        return artist_album_info["base64 cover"]

    #get album url from album_info table
    url = artist_album_info["album cover url"]

    #get all lyrics from all songs in an album
    alb_lyrics = []
    query = {"album": album}
    song_info = songInfo.find(query)
    for song in song_info:
        alb_lyrics.append(song['lyrics'])

    # format lyrics for wordcloud
    lyric = alb_lyrics
    lyric = " ".join(lyric)
    # removes words in brackets (ex: [chorus])
    # removes "\'", "-", "(", ")"
    lyric = re.sub(r'\[[^[]*\]', '', lyric)
    lyric = re.sub(r'\[[^[]*\]|\)|\(|\\*\'|\-', '', lyric)
    lyric = re.sub(r'[^\w\s]', ' ', lyric)
    tokens = lyric.split()
    for i in range(len(tokens)):
        if len(tokens[i]) >= 3:
            tokens[i] = tokens[i].lower()
    # read in common english words
    df = pd.read_csv("common_words.csv")
    eng_common_words = set(df.values.ravel())

    # remove common english words from tokens
    tokens = set(tokens)
    tokens = tokens.difference(eng_common_words)
    common_words += " ".join(tokens) + " "

    # empty check
    # if common_words == "" or " ":
    #     return None

    # use album cover as image mask
    im = Image.open(requests.get(url, stream=True).raw)
    image_mask = np.array(im)

    # generate word cloud
    wc = WordCloud(background_color="white", mask=image_mask,
                stopwords=stop_words, max_font_size=120, random_state=42)
    wc.generate(common_words)
    # generate image colors
    image_colors = ImageColorGenerator(image_mask)
    # plot the WordCloud image:
    fig, ax = plt.subplots()
    # recolor wordcloud
    try:
        ax.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
    # edge case album image not RGB
    except:
        ax.imshow(wc, interpolation="bilinear")
    # remove ugly axis lines
    ax.set_axis_off()

    # convert album cover and word cloud to base64 bitstring
    fig.savefig(my_stringIObytes, format='jpg')
    plt.close(fig)
    my_stringIObytes.seek(0)
    encoded_string = base64.b64encode(my_stringIObytes.read())

    # add encoded_string to album_info under 'base64 cover'
    albumInfo.update_one({'name': album}, {'$set': { 'base64 cover': encoded_string}})

    return encoded_string

def gen_wordcloud_one_song(url, lyric):
    # for encoding image to base64 MUST BE LOCAL VAR
    my_stringIObytes = io.BytesIO()
    # lyric string manipulation
    common_words = ''

    # removes words in brackets (ex: [chorus])
    # removes "\'", "-", "(", ")"
    lyric = re.sub(r'\[[^[]*\]', '', lyric)
    lyric = re.sub(r'\[[^[]*\]|\)|\(|\\*\'|\-', '', lyric)
    lyric = re.sub(r'[^\w\s]', ' ', lyric)
    tokens = lyric.split()
    for i in range(len(tokens)):
        if len(tokens[i]) >= 3:
            tokens[i] = tokens[i].lower()
    # read in common english words
    df = pd.read_csv("common_words.csv")
    eng_common_words = set(df.values.ravel())

    # remove common english words from tokens
    tokens = set(tokens)
    tokens = tokens.difference(eng_common_words)
    common_words += " ".join(tokens) + " "

    # use album cover as image mask
    im = Image.open(requests.get(url, stream=True).raw)
    image_mask = np.array(im)

    
    # generate word cloud
    wc = WordCloud(background_color="white", mask=image_mask,
                stopwords=stop_words, max_font_size=120, random_state=42)
    wc.generate(common_words)

    # create coloring from image
    image_colors = ImageColorGenerator(image_mask)
    # plot the WordCloud image:
    fig, ax = plt.subplots()
    # recolor wordcloud
    try:
        ax.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
    # edge case album cover not RGB
    except:
        ax.imshow(wc, interpolation="bilinear")
    # get rid of ugly axis lines
    ax.set_axis_off()

    # convert album cover and word cloud to base64 bitstring
    fig.savefig(my_stringIObytes, format='jpg')
    plt.close(fig)
    my_stringIObytes.seek(0)
    encoded_string = base64.b64encode(my_stringIObytes.read())

    return encoded_string

def calculate_sentiment(song_lyrics):
    #lyric_tokens = []
    #for entry in song_lyrics:
    #lyric = entry["lyrics"]
    fin_score = 0.0
    sentiment = 0
    lyric = str(song_lyrics)
    lyric = re.sub(r'\[[^[]*\]', '', lyric)
    #tokens = text_preprocessing(lyric)
    sid = SentimentIntensityAnalyzer()
    scores = sid.polarity_scores(lyric)
    #print(scores['pos'], scores['neg'], scores['neu'])
    fin_score = scores["compound"]
    if fin_score >= 0.4:
        sentiment = 1
    elif fin_score <= -0.4:
        sentiment = -1
    else:
        sentiment = 0
    return sentiment

##############################################

"""song_lyrics = ''
query = {"artist": "Taylor Swift"}
count = 1
for song in songInfo.find(query).sort("title"):
    if count <=20:
        song_lyrics = (song["lyrics"])
        print(song["title"])
        print(calculate_sentiment(song_lyrics))"""
#print(song_lyrics)


# TEST CASES
# one_song_lyrics = "A poor orphan girl named Maria Was walking to market one day She stopped for a rest by the roadside Where a bird with a broken wing lay A few moments passed till she saw it For it's feathers were covered with sand But soon clean and wrapped it was traveling In the warmth of Maria's small hand  She happily gave her last peso On a cage made of rushes and twine She fed it loose corn from the market And watched it grow stronger with time  Now the Christmas Eve service was coming And the church shone with tinsel and light And all of the townsfolk brought presents To lay by the manger that night There were diamonds and incense and perfumes In packages fit for a king But for one ragged bird in a small cage Maria had nothing to bring  She waited till just before midnight So no one could see her go in And crying she knelt by the manger For her gift was unworthy of Him  Then a voice spoke to her through the darkness Maria, what brings you to me If the bird in the cage is your offering Open the door, let me see Though she trembled, she did as he asked her And out of the cage the bird flew Soaring into the rafters On a wing that had healed good as new  Just then the midnight bells rang out And the little bird started to sing A song that no words could recapture Whose beauty was fit for a king  Now Maria felt blessed just to listen To that cascade of notes sweet and long As her offering was lifted to heaven By the very first nightingale's song"
# bits = generate_wordcloud("A Farmhouse Christmas","Joey + Rory")
# gen_wordcloud_one_song("https://i.scdn.co/image/ab67616d0000b2735b5599b0b6d80af33efbd63c",one_song_lyrics)
#calculate_sentiment(song_lyrics)


