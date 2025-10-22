import os
from pymongo import MongoClient
from dotenv import load_dotenv
from cleaner import clean

load_dotenv()

mongo_url = os.getenv("MONGO_URL")

client = MongoClient(mongo_url)

try:
    client.bulk_write(clean)
except:
    print("Error running MongoClient")
