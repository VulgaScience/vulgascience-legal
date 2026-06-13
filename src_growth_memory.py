import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

STORAGE = Path(os.getenv("STORAGE_ROOT", "./storage"))
LEARNING_DIR = STORAGE / "learning"
LEARNING_DIR.mkdir(parents=True, exist_ok=True)
PERFORMANCE_LOG = LEARNING_DIR / "performance_log.jsonl"
SUMMARY_FILE = LEARNING_DIR / "growth_summary.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path, payload):
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_events():
    if not PERFORMANCE_LOG.exists():
        return []
    events = []
    for line in PERFORMANCE_LOG.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def safe_ratio(num, den):
    return float(num) / float(den) if den else 0.0


def score_event(event):
    views = int(event.get("views", 0))
    likes = int(event.get("likes", 0))
    comments = int(event.get("comments", 0))
    shares = int(event.get("shares", 0))
    saves = int(event.get("saves", 0))
    avg_watch = float(event.get("avg_watch_seconds", 0.0))
    duration = max(float(event.get("duration_seconds", 1.0)), 1.0)
    completion = float(event.get("completion_rate", 0.0)) or safe_ratio(avg_watch, duration)
    engagement = safe_ratio(likes + comments * 3 + shares * 5 + saves * 4, views)
    share_rate = safe_ratio(shares, views)
    comment_rate = safe_ratio(comments, views)
    monetization = float(event.get("estimated_revenue", 0.0))
    return round(
        views * 0.15
        + views * min(completion, 1.5) * 0.35
        + views * engagement * 18
        + views * share_rate * 28
        + views * comment_rate * 18
        + monetization * 100,
        3,
    )


def record_performance(**kwargs):
    event = {
        "recorded_at": utc_now(),
        "video_id": kwargs.get("video_id"),
        "draft_id": kwargs.get("draft_id"),
        "topic": kwargs.get("topic"),
        "hook": kwargs.get("hook"),
        "format": kwargs.get("format"),
        "duration_seconds": float(kwargs.get("duration_seconds") or 0),
        "caption": kwargs.get("caption"),
        "hashtags": kwargs.get("hashtags") or [],
        "sound": kwargs.get("sound"),
        "views": int(kwargs.get("views") or 0),
        "likes": int(kwargs.get("likes") or 0),
        "comments": int(kwargs.get("comments") or 0),
        "shares": int(kwargs.get("shares") or 0),
        "saves": int(kwargs.get("saves") or 0),
        "avg_watch_seconds": float(kwargs.get("avg_watch_seconds") or 0),
        "completion_rate": float(kwargs.get("completion_rate") or 0),
        "followers_delta": int(kwargs.get("followers_delta") or 0),
        "estimated_revenue": float(kwargs.get("estimated_revenue") or 0),
    }
    event["growth_score"] = score_event(event)
    append_jsonl(PERFORMANCE_LOG, event)
    summarize()
    return event


def summarize():
    events = load_events()
    ranked = sorted(events, key=score_event, reverse=True)
    top = ranked[:10]
    summary = {
        "updated_at": utc_now(),
        "count": len(events),
        "top_videos": top,
        "winning_hooks": [item.get("hook") for item in top if item.get("hook")][:10],
        "winning_topics": [item.get("topic") for item in top if item.get("topic")][:10],
        "recommendations": build_recommendations(ranked),
    }
    SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def build_recommendations(ranked):
    if not ranked:
        return [
            "Publier d'abord 5 videos longues de 60-75s pour obtenir une base de comparaison.",
            "Suivre vues, retention, commentaires, partages et sauvegardes a 2h, 24h et 7j.",
        ]
    top = ranked[: max(1, min(5, len(ranked)))]
    avg_duration = sum(float(item.get("duration_seconds") or 0) for item in top) / len(top)
    avg_completion = sum(float(item.get("completion_rate") or 0) for item in top) / len(top)
    avg_share_rate = sum(safe_ratio(item.get("shares", 0), item.get("views", 0)) for item in top) / len(top)
    recs = [
        f"Durée cible actuelle: {avg_duration:.0f}s, à réviser après chaque lot de 5 vidéos.",
        f"Rétention moyenne des meilleurs contenus: {avg_completion:.2%}. Priorité si < 55%.",
        f"Taux de partage moyen des meilleurs contenus: {avg_share_rate:.2%}. Renforcer les moments 'à envoyer à un ami'.",
    ]
    if avg_completion < 0.55:
        recs.append("Raccourcir l'intro et placer l'exemple visuel avant 8 secondes.")
    if avg_share_rate < 0.01:
        recs.append("Ajouter un fait contre-intuitif ou un mini-test que les gens peuvent partager.")
    return recs


def main(argv=None):
    parser = argparse.ArgumentParser(description="Record TikTok performance and learn from it.")
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record")
    for name in [
        "video_id",
        "draft_id",
        "topic",
        "hook",
        "format",
        "caption",
        "sound",
    ]:
        record.add_argument(f"--{name}")
    record.add_argument("--hashtags", nargs="*", default=[])
    for name in [
        "duration_seconds",
        "views",
        "likes",
        "comments",
        "shares",
        "saves",
        "avg_watch_seconds",
        "completion_rate",
        "followers_delta",
        "estimated_revenue",
    ]:
        record.add_argument(f"--{name}", default=0)

    sub.add_parser("summary")

    args = parser.parse_args(argv)
    if args.command == "record":
        print(json.dumps(record_performance(**vars(args)), ensure_ascii=False, indent=2))
    elif args.command == "summary":
        print(json.dumps(summarize(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
