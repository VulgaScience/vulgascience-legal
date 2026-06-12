
"""
optimizer.py

Logique d'A/B testing et d'optimisation continue.
- Score initial : combine score_transcript + trend match (hashtags/queries match) + template quality.
- Collecte labels (views, like_rate) via analytics_collector, entraine un modèle simple (sklearn) pour prédire prob. de viralité.
- Fournit API : rank_candidates(candidates, n) -> top n candidates to render/publish.

Remarque : modèle léger (LogisticRegression) pour rapidité. Remplacer par XGBoost si besoin.
"""

import os
import json
from pathlib import Path
from datetime import datetime

STORAGE = Path(os.getenv("STORAGE_ROOT", "./storage"))
ANALYTICS_FILE = STORAGE / "analytics.json"
MODEL_FILE = STORAGE / "optimizer_model.json"
# optional sklearn
try:
    from sklearn.linear_model import LogisticRegression
    import numpy as np
except Exception:
    LogisticRegression = None
    np = None

def initial_score(candidate, trend_profile):
    """
    candidate: dict {
      'transcript_keywords': [..],
      'estimated_readability': float,
      'script_style': 'hooky'/'calm'/...
      'length_s': int
    }
    trend_profile: output from trend_analyzer.build_trend_profile()
    """
    score = 0
    # base: readability / length
    score += max(0, 50 - abs(candidate.get("length_s", 45) - 45))
    # keyword overlap with trend queries
    trends = " ".join(trend_profile.get("trending_phrases", [])).lower()
    kws = " ".join(candidate.get("transcript_keywords", [])).lower()
    overlap = sum(1 for w in candidate.get("transcript_keywords", []) if w.lower() in trends)
    score += overlap * 10
    # bonus for "hooky" style
    if candidate.get("script_style") == "hooky":
        score += 10
    return score

def rank_candidates(candidates, trend_profile, top_n=3):
    """
    candidates: list of candidate dicts
    returns top_n sorted by predicted score
    """
    # if no ML available, use initial_score
    scored = []
    for c in candidates:
        s = initial_score(c, trend_profile)
        scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:top_n]]

# Simple training loop: builds a logistic regression to predict "viral" (views > threshold)
def train_from_analytics():
    if LogisticRegression is None or np is None:
        print("skipping training: sklearn not installed")
        return None
    if not ANALYTICS_FILE.exists():
        print("no analytics to train on yet")
        return None
    data = json.loads(ANALYTICS_FILE.read_text())
    X = []
    y = []
    for rec in data.get("records", []):
        # build features
        features = []
        features.append(rec.get("init_score", 0))
        features.append(rec.get("length_s", 45))
        features.append(rec.get("script_style") == "hooky")
        features.append(rec.get("has_trend_overlap", 0))
        X.append(features)
        # label: viral if views per hour after publish > threshold
        views = rec.get("views", 0)
        hours = max(1.0, rec.get("hours_since_publish", 1.0))
        rate = views / hours
        y.append(1 if rate > 50 else 0)  # arbitrary threshold
    X = np.array(X)
    y = np.array(y)
    if len(y) < 10:
        print("not enough examples to train (need >=10)")
        return None
    clf = LogisticRegression()
    clf.fit(X, y)
    # persist coefficients (simple)
    model = {"coef": clf.coef_.tolist(), "intercept": clf.intercept_.tolist()}
    MODEL_FILE.write_text(json.dumps(model))
    print("trained model and saved to", MODEL_FILE)
    return model

if __name__ == "__main__":
    # small demo
    trend_profile = {"trending_phrases": ["ai", "chatgpt", "space", "black hole"]}
    cands = [
        {"transcript_keywords": ["AI", "model"], "length_s": 45, "script_style": "hooky"},
        {"transcript_keywords": ["algorithm", "theorem"], "length_s": 70, "script_style": "calm"},
    ]
    print("Ranking:", rank_candidates(cands, trend_profile))
