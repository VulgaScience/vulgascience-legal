
"""
analytics_collector.py

Récupère les analytics des posts publiés (via TikTok API si dispo) ou permet l'entrée manuelle / ingestion.
Stocke dans storage/analytics.json un historique minimal:
{
  "records": [
    {
      "video_name": "...",
      "publish_time": "...",
      "views": 1234,
      "likes": 123,
      "shares": 10,
      "comments": 5,
      "hours_since_publish": 3,
      "init_score": 78,
      "script_style": "hooky",
      ...
    }
  ]
}
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
STORAGE = Path(os.getenv("STORAGE_ROOT", "./storage"))
ANALYTICS_FILE = STORAGE / "analytics.json"
ANALYTICS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_analytics():
    if ANALYTICS_FILE.exists():
        return json.loads(ANALYTICS_FILE.read_text())
    else:
        return {"records": []}

def save_analytics(obj):
    ANALYTICS_FILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2))

def append_record(rec):
    data = load_analytics()
    data.setdefault("records", []).append(rec)
    save_analytics(data)
    return True

# Example helper: synthetic ingestion for testing
def ingest_sample(video_name, views, likes, shares, comments, init_score, script_style):
    rec = {
        "video_name": video_name,
        "publish_time": datetime.now(timezone.utc).isoformat(),
        "views": views,
        "likes": likes,
        "shares": shares,
        "comments": comments,
        "hours_since_publish": 1.0,
        "init_score": init_score,
        "script_style": script_style,
        "has_trend_overlap": 1 if init_score > 50 else 0
    }
    append_record(rec)
    return rec

if __name__ == "__main__":
    print("Ingesting sample analytics...")
    print(ingest_sample("demo_video.mp4", 1200, 150, 10, 5, 78, "hooky"))
