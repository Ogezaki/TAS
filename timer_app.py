import argparse, csv, json, ssl
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify

APP_DIR = Path(__file__).parent.resolve()
DATA_DIR = APP_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"
LOG_FILE = DATA_DIR / "runs_log.csv"
PRICES_FILE = APP_DIR / "prices_essence.json"

app = Flask(__name__, template_folder=str(APP_DIR / "templates"), static_folder=str(APP_DIR / "static"))

# Importer et enregistrer le blueprint essence
from essence_api import essence_bp
app.register_blueprint(essence_bp)

def log(msg): print(msg, flush=True)

def ensure_dirs():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("w", newline="", encoding="utf-8") as f:
            import csv as _csv
            w = _csv.writer(f)
            w.writerow(["timestamp_iso","athlete","session_id","segment_id","segment_name","length_m_est","elapsed_ms","elapsed_hms","buffer_m","distance_m","avg_kmh","max_kmh","pace_min_km","trace_json_path"])

@app.get("/")
def index():
    log("[HTTP] GET / -> index.html")
    return render_template("index.html")

@app.get("/details")
def details():
    log("[HTTP] GET /details -> details.html")
    return render_template("details.html")

@app.post("/api/heartbeat")
def heartbeat():
    data = request.get_json(silent=True) or {}
    log(f"[API] heartbeat {data}")
    return jsonify(ok=True)

@app.post("/api/refresh-gas-prices")
def refresh_gas_prices():
    """
    Rafraîchit les prix d'essence en scrapant le site
    """
    try:
        from scraper_essence import scrape_essence_quebec
        log("[API] Refreshing gas prices from EssenceQuébec...")
        prices = scrape_essence_quebec()
        
        if prices:
            with PRICES_FILE.open('w', encoding='utf-8') as f:
                json.dump(prices, f, ensure_ascii=False, indent=2)
            log(f"[API] Gas prices refreshed: {len(prices)} regions found")
            return jsonify(ok=True, regions_count=len(prices))
        else:
            log("[API] Failed to scrape gas prices")
            return jsonify(ok=False, error="Failed to scrape prices"), 500
    except Exception as e:
        log(f"[API] Error refreshing gas prices: {e}")
        return jsonify(ok=False, error=str(e)), 500

@app.post("/api/save_free_run")
def save_free_run():
    ensure_dirs()
    payload = request.get_json(force=True, silent=True) or {}
    now = datetime.now()
    day = now.strftime("%Y-%m-%d")
    ts = now.strftime("%Y%m%d_%H%M%S")
    athlete = (payload.get("athlete") or "user").replace("/", "_")

    out_dir = RUNS_DIR / day / athlete
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{athlete}_{ts}"
    json_path = out_dir / f"{base}.json"
    gj_path = out_dir / f"{base}.geojson"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    trace = payload.get("trace") or []
    gj = {"type":"FeatureCollection","features":[]}
    if trace:
        coords = [[p.get("lon"), p.get("lat")] for p in trace if "lat" in p and "lon" in p]
        gj["features"].append({"type":"Feature","properties":{"name":base},"geometry":{"type":"LineString","coordinates":coords}})
    with gj_path.open("w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False, indent=2)

    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        import csv as _csv
        w = _csv.DictWriter(f, fieldnames=["timestamp_iso","athlete","session_id","segment_id","segment_name","length_m_est","elapsed_ms","elapsed_hms","buffer_m","distance_m","avg_kmh","max_kmh","pace_min_km","trace_json_path"])
        row = {
            "timestamp_iso": now.isoformat(),
            "athlete": athlete,
            "session_id": payload.get("session_id",""),
            "segment_id": payload.get("segment_id",""),
            "segment_name": payload.get("segment_name",""),
            "length_m_est": payload.get("length_m_est",""),
            "elapsed_ms": payload.get("elapsed_ms",0),
            "elapsed_hms": payload.get("elapsed_hms",""),
            "buffer_m": payload.get("buffer_m",0),
            "distance_m": payload.get("distance_m",""),
            "avg_kmh": payload.get("avg_kmh",""),
            "max_kmh": payload.get("max_kmh",""),
            "pace_min_km": payload.get("pace_min_km",""),
            "trace_json_path": str(json_path).replace('\\','/')
        }
        w.writerow(row)

    saved_path = str(json_path).replace('\\','/')
    log("[API] save_free_run -> " + saved_path)
    return jsonify(ok=True, saved=saved_path)

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--https", type=int, default=0)
    ap.add_argument("--https-port", type=int, default=8443)
    ap.add_argument("--cert", default="cert.pem")
    ap.add_argument("--key", default="key.pem")
    return ap.parse_args()

if __name__ == "__main__":
    ensure_dirs()
    args = parse_args()
    if args.https:
        try:
            from pathlib import Path as _P
            if _P(args.cert).exists() and _P(args.key).exists():
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ctx.load_cert_chain(args.cert, args.key)
                log(f"[TAS] HTTPS on https://0.0.0.0:{args.https_port}")
                app.run(host=args.host, port=args.https_port, ssl_context=ctx)
            else:
                log(f"[TAS] Trying adhoc TLS on https://0.0.0.0:{args.https_port} (requires cryptography)")
                app.run(host=args.host, port=args.https_port, ssl_context='adhoc')
        except Exception as e:
            log(f"[TAS] TLS failed: {e}")
            log(f"[TAS] Fallback to HTTP on http://0.0.0.0:{args.port}")
            app.run(host=args.host, port=args.port)
    else:
        log(f"[TAS] HTTP on http://0.0.0.0:{args.port}")
        app.run(host=args.host, port=args.port)
