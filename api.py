import math
import os
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise RuntimeError("No Mongo URL provided.")

client = MongoClient(MONGO_URL)
db = client.get_database("water_quality_data")
collect = db.get_collection("asv_1")

TEMP_FIELD = "Temperature (c)"
SAL_FIELD = "Salinity (ppt)"
ODO_FIELD = "ODO mg/L"

TIME_FIELD = "Time hh:mm:ss"
TIME_FIELD_SECONDARY = "Time"

DATE_FIELD = "Date m/d/y   "
DATE_FIELD_SECONDARY = "Date"

NUMERIC_FIELDS = [TEMP_FIELD, SAL_FIELD, ODO_FIELD]

ALIAS_TO_FIELD = {
    "temp": TEMP_FIELD,
    "sal": SAL_FIELD,
    "odo": ODO_FIELD,
    "time": TIME_FIELD,
    "date": DATE_FIELD,
}
app = Flask(__name__)
CORS(app)

# build the MongoDB filters using the ranges in request arguments
def build_value_filters(args):
    q = {}
    for alias, field in ALIAS_TO_FIELD.items():
        lo = args.get(f"min_{alias}", type=float)
        hi = args.get(f"max_{alias}", type=float)
        if lo is not None or hi is not None:
            rng = {}
            if lo is not None:
                rng["$gte"] = lo
            if hi is not None:
                rng["$lte"] = hi
            q[field] = rng
    return q

# build timestamps from the date/time columns
def parse_timestamp(doc):
    d = doc.get(DATE_FIELD)
    t = doc.get(TIME_FIELD)

    return datetime.strptime(f"{d} {t}", "%m/%d/%y %H:%M:%S")

# filter documents that don't match the timestamp range
def filter_by_time(docs, start, end):
    out = []
    for d in docs:
        ts = parse_timestamp(d)
        if start and (ts is None or ts < start):
            continue
        if end and (ts is None or ts > end):
            continue
        out.append(d)
    return out

def add_iso_timestamp(doc):
    if "timestamp" in doc and doc["timestamp"]:
        return doc
    ts = parse_timestamp(doc)

    if ts:
        doc["timestamp"] = ts.isoformat()
    else:
        doc["timestamp"] = None

    return doc

def _to_float(x):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return None
        return float(x)
    except Exception:
        return None

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.get("/api/observations")
def observations():
    limit = request.args.get("limit", default=100, type=int)

    if limit > 1000:
        limit = 1000
    elif limit < 1:
        limit = 1

    skip = request.args.get("skip", default=0, type=int)

    if skip < 0:
        skip = 0

    start_str = request.args.get("start")
    end_str = request.args.get("end")
    start_dt = None
    end_dt = None
    try:
        if start_str:
            start_dt = datetime.fromisoformat(start_str)
        if end_str:
            end_dt = datetime.fromisoformat(end_str)
    except Exception:
        start_dt = None
        end_dt = None

    min_temp = request.args.get("min_temp", default=-10, type=float)
    max_temp = request.args.get("max_temp", default=60, type=float)

    min_sal = request.args.get("min_sal", default=0, type=float)
    max_sal = request.args.get("max_sal", default=500, type=float)

    min_odo = request.args.get("min_odo", default=0, type=float)
    max_odo = request.args.get("max_odo", default=20, type=float)

    q = build_value_filters(request.args)

    proj = {"_id": 0}
    cursor = collect.find(q, proj).skip(skip).limit(limit * 4)
    docs = list(cursor)

    if start_dt or end_dt:
        docs = filter_by_time(docs, start_dt, end_dt)

    docs = docs[:limit]

    items = []
    for d in docs:
        d = add_iso_timestamp(dict(d))
        for f in NUMERIC_FIELDS:
            if f in d:
                d[f] = _to_float(d.get(f))
        items.append(d)

    return jsonify({"count": len(items), "items": items}), 200

@app.get("/api/stats")
def stats():
    return "stats"

@app.get("/api/outliers")
def outliers():
    return "outliers"

if __name__ == "__main__":
    app.run(port=5000, debug=True)