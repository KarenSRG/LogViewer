from pymongo import MongoClient

connect_string = "localhost:27017"
mongodb = MongoClient(connect_string)
db = mongodb["main"]

for i in ["insize", "gandreich", "elwycco", "mooniverse", "cemka", "alcoreru", "unclebjorn", "shroud", "kal_zer",
          "streamers", "streams"]:
    db.drop_collection(i)
db.create_collection("streamers")
db.create_collection("streams")
