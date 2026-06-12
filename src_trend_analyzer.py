
"""
trend_analyzer.py

Collecte les tendances (Google Trends, YouTube trending, option de scraping TikTok)
Retourne un objet "trend_profile" contenant :
- top_hashtags: list[str]
- top_music: list[str]
- top_queries: list[str]
- trending_phrases: list[str]
- timestamp: iso

Notes:
- Configure les clés dans .env si nécessaire (YOUTUBE_API_KEY).
- Pour TikTok scraping il faudra ajouter un USER_AGENT valide et accepter les risques (page HTML change souvent).
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

# optional libs
try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None

try:
    from googleapiclient.discovery import build
except Exception:
    build = None

import requests
from bs4 import BeautifulSoup

STORAGE = Path(os.getenv("STORAGE_ROOT", "./storage"))
TREND_DIR = STORAGE / "trends"
TREND_DIR.mkdir(parents=True, exist_ok=True)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def google_trends_top_queries(geo="FR", timeframe="now 1-d"):
    if TrendReq is None:
        return []
    pytrends = TrendReq(hl="fr-FR", tz=360)
    try:
        pytrends.build_payload(kw_list=["science", "recherche"], timeframe=timeframe, geo=geo)
        related = pytrends.related_queries()
        queries = []
        for k, v in related.items():
            top = v.get("top")
            if top is not None:
                for q in top["query"].tolist()[:5]:
                    queries.append(q)
        return list(dict.fromkeys(queries))[:20]
    except Exception:
        return []

def youtube_trending_terms(max_results=10):
    if build is None or not YOUTUBE_API_KEY:
        return []
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        req = youtube.videos().list(part="snippet", chart="mostPopular", regionCode="US", maxResults=max_results)
        res = req.execute()
        terms = []
        for item in res.get("items", []):
            title = item["snippet"]["title"]
            for token in title.split():
                if len(token) > 3:
                    terms.append(token.strip().lower())
        # simple frequency sort
        freq = {}
        for t in terms:
            freq[t] = freq.get(t, 0) + 1
        sorted_terms = [k for k, _ in sorted(freq.items(), key=lambda x: -x[1])]
        return sorted_terms[:20]
    except Exception:
        return []

def tiktok_trending_scrape(top_n=20, country="fr"):
    """
    Simple scraping of TikTok discover/trending page.
    Be aware: scraping may break / be against ToS. Use responsibly.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url = f"https://www.tiktok.com/discover"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        hashtags = []
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if "/tag/" in href and a.text:
                hashtags.append(a.text.strip().lstrip("#"))
        # dedupe preserve order
        hashtags = list(dict.fromkeys(hashtags))
        return hashtags[:top_n]
    except Exception:
        return []

def build_trend_profile():
    profile = {
        "top_hashtags": [],
        "top_music": [],
        "top_queries": [],
        "trending_phrases": [],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    try:
        profile["top_queries"] = google_trends_top_queries() or youtube_trending_terms()
    except Exception:
        pass
    try:
        profile["top_hashtags"] = tiktok_trending_scrape()[:20]
    except Exception:
        profile["top_hashtags"] = []
    # placeholder for music (requires TikTok API or 3rd party)
    profile["top_music"] = []  # To be filled if you have access to music trends
    # smart extraction: take top 10 queries and extract phrases
    profile["trending_phrases"] = profile["top_queries"][:10]
    # persist
    out = TREND_DIR / (datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + ".json")
    out.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
    return profile

if __name__ == "__main__":
    print("Building trend profile...")
    p = build_trend_profile()
    print("Profile:", json.dumps(p, indent=2, ensure_ascii=False))
