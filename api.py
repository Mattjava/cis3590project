import os
from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise RuntimeError("No Mongo URL provided.")

client = MongoClient(MONGO_URL)
db = client.get_database("water_quality_data")
collect = db.get_collection("asv_1")

app = Flask(__name__)
CORS(app)

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.get("/api/observations")
def observations():
    return "observations"

@app.get("/api/stats")
def stats():
    return "stats"

@app.get("/api/outliers")
def outliers():
    return "outliers"

if __name__ == "__main__":
    app.run(port=5000, debug=True)