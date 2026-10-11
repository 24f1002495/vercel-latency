from http.server import BaseHTTPRequestHandler
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
with open(DATA_PATH) as f:
    DATA = json.load(f)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Content-Type": "application/json",
}

def compute(regions, threshold_ms):
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
    return result

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        regions = body.get("regions", [])
        threshold_ms = body.get("threshold_ms", 180)
        result = compute(regions, threshold_ms)
        response = json.dumps(result).encode()
        self.send_response(200)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)