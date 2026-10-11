from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data relative to this file
DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
with open(DATA_PATH) as f:
    DATA = json.load(f)

@app.post("/api")
async def latency_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        records = [r for r in DATA if r["region"] == region]
        if not records:
            result[region] = {"avg_latency": None, "p95_latency": None, "avg_uptime": None, "breaches": 0}
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        avg_latency = round(sum(latencies) / len(latencies), 4)
        avg_uptime = round(sum(uptimes) / len(uptimes), 4)
        breaches = sum(1 for l in latencies if l > threshold_ms)

        sorted_lat = sorted(latencies)
        idx = 0.95 * (len(sorted_lat) - 1)
        lo, hi = int(idx), min(int(idx) + 1, len(sorted_lat) - 1)
        p95 = round(sorted_lat[lo] + (sorted_lat[hi] - sorted_lat[lo]) * (idx - lo), 4)

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return JSONResponse(content=result)

@app.options("/api")
async def options():
    return JSONResponse(content={}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    })
