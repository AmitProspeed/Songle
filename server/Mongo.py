from pymongo import MongoClient
from bson.objectid import ObjectId

#establishing connection with MongoDB
client = MongoClient("mongodb+srv://testUser:bigData@cluster0.xn34j.mongodb.net")
db = client["MusicDataset"]
songInfo = db["songInfo"]

#verifying if database exists/created
dblist = client.list_database_names()
if "MusicDataset" in dblist:
  print("The database exists.")
else:
    print("Not found")

#format for entering a song into the SongInfo Table
"""song = {
    "_id" : 1,
    "title" : "In the end",
    "lyrics" : "One thing I don't know why " +
               "It doesn't even matter how hard you try Keep that in mind, " +
               "I designed this rhyme " + "To explain in due time",
    "genre" : ["Rap rock", "Hard rock"],
    "artist" : "Linkin Park",
    "album" : "Hybrid Theory",
    "year" : 2000
}

songInfo.insert_one(song) #use insert_many when more than one insertion is involved
"""

#searching for single entry / multiple entries
query = {"_id": "607754466741a45bc20e4258"}
#song = songInfo.find_one(query)
for song in songInfo.find(query):
    print(song)

#deleting entries
entry = songInfo.delete_many({"title" : "random"})
print(entry.deleted_count, " entries deleted.")
