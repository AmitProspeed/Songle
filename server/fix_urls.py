client = pymongo.MongoClient("mongodb+srv://testUser:bigData@cluster0.xn34j.mongodb.net")
db = client["MusicDataset"]
songInfo = db["songInfo"]