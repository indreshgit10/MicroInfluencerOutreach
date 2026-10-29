"""
REST API Backend for Automated Micro-Influencer Outreach System
Serves API endpoints for pipeline execution, dataset inspection, and interactive web dashboard.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, request, send_file, render_template, send_from_directory
from flask_cors import CORS

from backend.config import (
    BASE_DIR, DATA_DIR, RAW_DATA_PATH, RAW_DATA_CSV,
    FILTERED_DATA_PATH, FILTERED_DATA_CSV,
    ENRICHED_DATA_PATH, ENRICHED_DATA_CSV,
    OUTREACH_DATA_PATH, OUTREACH_DATA_CSV,
    TRACKER_DATA_PATH, TRACKER_DATA_CSV,
    DEFAULT_TARGET_NICHE, MIN_FOLLOWERS, MAX_FOLLOWERS, MIN_ENGAGEMENT_RATE,
    LLM_PROVIDER, SENDING_MODE
)
from backend.pipeline.discovery import InfluencerDiscoveryEngine
from backend.pipeline.filter_classify import InfluencerFilterClassifier
from backend.pipeline.enrichment import InfluencerEnrichmentEngine
from backend.pipeline.personalization import MessagePersonalizationEngine
from backend.pipeline.sending_layer import OutreachSendingLayer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("API")

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "frontend" / "templates"),
    static_folder=str(BASE_DIR / "frontend" / "static")
)
CORS(app)

DATA_FILES = {
    "discovered": (RAW_DATA_PATH, RAW_DATA_CSV),
    "filtered": (FILTERED_DATA_PATH, FILTERED_DATA_CSV),
    "enriched": (ENRICHED_DATA_PATH, ENRICHED_DATA_CSV),
    "outreach": (OUTREACH_DATA_PATH, OUTREACH_DATA_CSV),
    "tracker": (TRACKER_DATA_PATH, TRACKER_DATA_CSV),
}

def load_json_safe(path: Path) -> list:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "EDXSO Micro-Influencer Outreach Engine"})

@app.route("/api/stats")
def get_stats():
    discovered = load_json_safe(RAW_DATA_PATH)
    filtered = load_json_safe(FILTERED_DATA_PATH)
    enriched = load_json_safe(ENRICHED_DATA_PATH)
    outreach = load_json_safe(OUTREACH_DATA_PATH)
    tracker = load_json_safe(TRACKER_DATA_PATH)

    passed_count = sum(1 for f in filtered if f.get("passed"))
    emails_available = sum(1 for e in enriched if e.get("has_valid_email") and e.get("passed"))
    sent_or_simulated = sum(1 for t in tracker if t.get("status") in ["SENT", "SIMULATED", "DM_READY_FOR_DISPATCH"])

    return jsonify({
        "total_discovered": len(discovered),
        "total_filtered": len(filtered),
        "passed_qualified": passed_count,
        "disqualified": len(filtered) - passed_count,
        "emails_available": emails_available,
        "personalized_pitches": len(outreach),
        "outreach_tracked": len(tracker),
        "sent_or_simulated": sent_or_simulated,
        "niche": DEFAULT_TARGET_NICHE,
        "sending_mode": SENDING_MODE
    })

@app.route("/api/data/<dataset_name>")
def get_dataset(dataset_name: str):
    if dataset_name not in DATA_FILES:
        return jsonify({"error": f"Dataset '{dataset_name}' not found"}), 404
    json_path, _ = DATA_FILES[dataset_name]
    data = load_json_safe(json_path)
    return jsonify(data)

@app.route("/api/export/<dataset_name>/<fmt>")
def export_dataset(dataset_name: str, fmt: str):
    if dataset_name not in DATA_FILES:
        return jsonify({"error": "Dataset not found"}), 404
    json_path, csv_path = DATA_FILES[dataset_name]
    target_file = csv_path if fmt.lower() == "csv" else json_path
    if not target_file.exists():
        return jsonify({"error": f"File for {dataset_name} has not been generated yet"}), 404
    return send_file(target_file, as_attachment=True)

@app.route("/api/pipeline/run", methods=["POST"])
def run_pipeline_api():
    body = request.get_json() or {}
    target_niche = body.get("niche", DEFAULT_TARGET_NICHE)
    min_followers = int(body.get("min_followers", MIN_FOLLOWERS))
    max_followers = int(body.get("max_followers", MAX_FOLLOWERS))
    min_engagement = float(body.get("min_engagement", MIN_ENGAGEMENT_RATE))
    simulate = body.get("simulate", True)

    try:
        # Stage 1: Discovery
        disc_engine = InfluencerDiscoveryEngine(target_niche=target_niche)
        discovered = disc_engine.run_discovery(min_count=50)

        # Stage 2: Filtering
        filter_engine = InfluencerFilterClassifier(
            target_category=target_niche,
            min_followers=min_followers,
            max_followers=max_followers,
            min_engagement_rate=min_engagement
        )
        filtered = filter_engine.run_filtering(discovered)

        # Stage 3: Enrichment
        enrich_engine = InfluencerEnrichmentEngine()
        enriched = enrich_engine.run_enrichment(filtered)

        # Stage 4: Personalization
        pers_engine = MessagePersonalizationEngine()
        outreach = pers_engine.run_personalization(enriched)

        # Stage 5: Sending
        sending_engine = OutreachSendingLayer(mode="simulation" if simulate else SENDING_MODE)
        tracker = sending_engine.process_outreach(outreach, simulate_all=simulate)

        return jsonify({
            "success": True,
            "message": "Full pipeline executed successfully",
            "counts": {
                "discovered": len(discovered),
                "filtered_passed": sum(1 for f in filtered if f.get("passed")),
                "filtered_failed": sum(1 for f in filtered if not f.get("passed")),
                "enriched": len(enriched),
                "outreach_generated": len(outreach),
                "tracker_records": len(tracker)
            }
        })
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/outreach/record_dm_dispatch", methods=["POST"])
def record_dm_dispatch():
    body = request.get_json() or {}
    name = body.get("name")
    if not name:
        return jsonify({"error": "Influencer name required"}), 400

    tracker = load_json_safe(TRACKER_DATA_PATH)
    updated = False
    for item in tracker:
        if item.get("influencer") == name:
            item["status"] = "DM_COPIED_AND_DISPATCHED"
            item["delivery_details"] = "Message copied to clipboard and dispatched to creator profile."
            updated = True
            break
    
    if updated:
        with open(TRACKER_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(tracker, f, indent=2, ensure_ascii=False)
        return jsonify({"success": True, "message": f"Recorded DM dispatch for {name}"})
    return jsonify({"error": "Influencer record not found in tracker"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
