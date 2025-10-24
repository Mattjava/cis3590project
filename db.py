import os, json
from pymongo import MongoClient
from dotenv import load_dotenv
from cleaner import result

load_dotenv()

mongo_url = os.getenv("MONGO_URL")

client = MongoClient(mongo_url)

db = client.get_database("water_quality_data")
collect = db.get_collection("asv_1")


for filename in result:
    data = result[filename].to_dict('records')
    collect.insert_many(data)

