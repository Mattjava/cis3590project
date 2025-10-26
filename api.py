import math
import os
import statistics
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
DATE_FIELD = "Date m/d/y   "

LAT_FIELD = "Latitude"
LON_FIELD = "Longitude"

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

def summarize(values):
    values = [v for v in values if v is not None and not math.isnan(v)]

    if not values:
        return {"count": 0, "mean": None, "min": None, "max": None, "p25": None, "p50": None, "p75": None}

    vals = sorted(values)
    n = len(vals)
    mean_v = statistics.fmean(vals)

    def pct(p):
        k = max(1, math.ceil(p * n)) - 1
        return vals[k]

    return {
        "count": n,
        "mean": mean_v,
        "min": vals[0],
        "max": vals[-1],
        "p25": pct(0.25),
        "p50": pct(0.50),
        "p75": pct(0.75),
    }

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
    q = build_value_filters(request.args)
    proj = {"_id": 0}

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
        pass

    docs = list(collect.find(q, proj))
    if start_dt or end_dt:
        proj_plus = {**proj, DATE_FIELD: 1, TIME_FIELD: 1}
        docs = list(collect.find(q, proj_plus))
        docs = filter_by_time(docs, start_dt, end_dt)

    out = {}
    for field in NUMERIC_FIELDS:
        vals = [_to_float(d.get(field)) for d in docs]
        out[field] = summarize([v for v in vals if v is not None])

    return jsonify(out), 200

@app.get("/api/outliers")
def outliers():
    field_param = request.args.get("field", default="temp").lower().strip()
    field = ALIAS_TO_FIELD.get(field_param, field_param)
    if field not in NUMERIC_FIELDS:
        return jsonify({"error": f"'{field_param}' is not a numeric field. Use: temperature|salinity|odo"}), 400

    method = request.args.get("method", default="iqr").lower().strip()
    k = request.args.get("k", type=float)
    if k is None:
        k = 1.5 if method == "iqr" else 3.0

    q = build_value_filters(request.args)

    proj = {
        "_id": 0,
        field: 1,
        TEMP_FIELD: 1, SAL_FIELD: 1, ODO_FIELD: 1,
        LAT_FIELD: 1, LON_FIELD: 1,
        DATE_FIELD: 1, TIME_FIELD: 1,
    }
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
        pass

    docs = list(collect.find(q, proj))
    if start_dt or end_dt:
        docs = filter_by_time(docs, start_dt, end_dt)

    values = [_to_float(d.get(field)) for d in docs]
    values = [v for v in values if v is not None and not math.isnan(v)]
    if not values:
        return jsonify({"count": 0, "items": [], "thresholds": None}), 200

    thresholds = {}
    if method == "iqr":
        vals = sorted(values)
        n = len(vals)

        def pct(p):
            kidx = max(1, math.ceil(p * n)) - 1
            return vals[kidx]

        q1, q3 = pct(0.25), pct(0.75)
        iqr = q3 - q1
        low = q1 - k * iqr
        high = q3 + k * iqr

        def is_outlier(v):
            return v < low or v > high

        thresholds = {"method": "iqr", "k": k, "low": low, "high": high}

    elif method in ("z", "zscore", "z-score"):
        mean_v = statistics.fmean(values)
        sd = statistics.pstdev(values) if len(values) > 1 else 0.0

        if sd == 0.0:
            return jsonify({"count": 0, "items": [], "thresholds": {"method": "zscore", "k": k, "mean": mean_v, "sd": sd}}), 200
        def is_outlier(v):
            return abs((v - mean_v) / sd) > k
        thresholds = {"method": "zscore", "k": k, "mean": mean_v, "sd": sd}
    else:
        return jsonify({"error": "method must be 'iqr' or 'zscore'"}), 400

    flagged = []
    for d in docs:
        v = _to_float(d.get(field))
        if v is None or math.isnan(v):
            continue
        if is_outlier(v):
            flagged.append(add_iso_timestamp(dict(d)))

    return jsonify({"count": len(flagged), "field": field, "items": flagged, "thresholds": thresholds}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)