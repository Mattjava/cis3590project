import os, json, pandas
from pymongo import MongoClient
from dotenv import load_dotenv

data_files = os.listdir("data")

data_files = [file for file in data_files if file.find("CLEANED") != -1]

load_dotenv()

mongo_url = os.getenv("MONGO_URL")

client = MongoClient(mongo_url)

db = client.get_database("water_quality_data")
collect = db.get_collection("asv_1")


for filename in data_files:
    print("Uploading " + filename)
    dt = pandas.read_csv("data/" + filename)
    data = dt.to_dict('records')
    collect.insert_many(data)

print("Finished saving data")