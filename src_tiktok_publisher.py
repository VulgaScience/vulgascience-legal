
"""
tiktok_publisher.py

Squelette d'intégration avec TikTok for Developers (OAuth + upload + publish).
Tu dois renseigner TIKTOK_CLIENT_KEY/SECRET/REFRESH_TOKEN dans .env.
La partie OAuth dépend de l'app et des permissions — ce module fournit des fonctions de base à compléter.

Fallback: si pas d'accès API, le système déposera les vidéos prêtes dans OUTBOX (déjà géré)
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TIKTOK_REFRESH_TOKEN = os.getenv("TIKTOK_REFRESH_TOKEN")
STORAGE = Path(os.getenv("STORAGE_ROOT", "./storage"))
OUTBOX = STORAGE / "outbox"
PUBLISHED = STORAGE / "published"
OUTBOX.mkdir(parents=True, exist_ok=True)
PUBLISHED.mkdir(parents=True, exist_ok=True)

# Endpoints (subject to change; consult TikTok docs)
TOKEN_URL = "https://open-api.tiktok.com/oauth/access_token/"
UPLOAD_URL = "https://open-api.tiktok.com/video/upload/"
PUBLISH_URL = "https://open-api.tiktok.com/video/publish/"

def refresh_access_token():
    if not (TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET and TIKTOK_REFRESH_TOKEN):
        raise RuntimeError("TikTok credentials missing")
    # Placeholder: actual flow depends on OAuth implementation and token types
    resp = requests.post(TOKEN_URL, data={
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": TIKTOK_REFRESH_TOKEN
    })
    if resp.status_code == 200:
        data = resp.json()
        access_token = data.get("access_token")
        return access_token
    else:
        raise RuntimeError("Failed to refresh token: " + resp.text)

def upload_video_file(access_token, video_path):
    """
    Upload video and return upload_id (simplified)
    """
    files = {"video": open(video_path, "rb")}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.post(UPLOAD_URL, headers=headers, files=files)
    if resp.status_code == 200:
        return resp.json().get("data", {}).get("video_id")
    else:
        raise RuntimeError("Upload failed: " + resp.text)

def publish_video(access_token, video_id, caption, hashtags=None):
    payload = {
        "video_id": video_id,
        "text": caption + (" " + " ".join(["#"+h for h in (hashtags or [])]) if hashtags else "")
    }
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    resp = requests.post(PUBLISH_URL, headers=headers, json=payload)
    if resp.status_code == 200:
        return resp.json().get("data", {})
    else:
        raise RuntimeError("Publish failed: " + resp.text)

def publish_from_path(video_path, caption, hashtags=None):
    try:
        token = refresh_access_token()
    except Exception as e:
        print("TikTok API not configured or refresh failed:", e)
        # fallback: move to OUTBOX (already done elsewhere)
        return {"status": "outbox", "path": str(video_path)}
    try:
        vid = upload_video_file(token, video_path)
        res = publish_video(token, vid, caption, hashtags)
        # move file to published
        dest = PUBLISHED / video_path.name
        video_path.replace(dest)
        return {"status": "published", "tiktok_id": res.get("video_id")}
    except Exception as e:
        print("Publish error:", e)
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    # test (will fallback to outbox if not configured)
    print(publish_from_path(Path("example.mp4"), "Test caption #science", hashtags=["science","research"]))
