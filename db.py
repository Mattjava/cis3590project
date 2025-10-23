import os, json
from pymongo import MongoClient
from dotenv import load_dotenv
from cleaner import result

load_dotenv()

mongo_url = os.getenv("MONGO_URL")

client = MongoClient(mongo_url)

db = client.get_database("water_data")


for filename in result:
    collection = db.get_collection(filename)
    data = result[filename].to_dict('records')
    collection.insert_many(data)

