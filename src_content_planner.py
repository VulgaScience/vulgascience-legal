import argparse
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONTENT_FILE = ROOT / "content" / "production_queue.json"
STORAGE = Path(os.getenv("STORAGE_ROOT", "./storage"))
GROWTH_SUMMARY = STORAGE / "learning" / "growth_summary.json"

DEFAULT_WEIGHTS = {
    "trend_fit": 1.2,
    "science_fit": 1.1,
    "search_value": 1.0,
    "retention_hook": 1.4,
    "demo_potential": 1.1,
    "comment_trigger": 1.2,
    "monetization_fit": 1.5,
}


def load_json(path, default):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def growth_adjustment(candidate, summary):
    if not summary or not summary.get("count"):
        return 0.0, []

    notes = []
    adjustment = 0.0
    topic = candidate.get("topic", "").lower()
    hook = candidate.get("hook", "").lower()

    winning_topics = [str(item).lower() for item in summary.get("winning_topics", [])]
    winning_hooks = [str(item).lower() for item in summary.get("winning_hooks", [])]

    if any(word in topic for word in winning_topics):
        adjustment += 1.5
        notes.append("matches previous winning topic")
    if any(word in hook for word in winning_hooks):
        adjustment += 1.0
        notes.append("matches previous winning hook pattern")

    return adjustment, notes


def score_candidate(candidate, summary=None, weights=None):
    weights = weights or DEFAULT_WEIGHTS
    scores = candidate.get("scores", {})
    base = sum(float(scores.get(key, 0)) * weight for key, weight in weights.items())
    adjustment, notes = growth_adjustment(candidate, summary or {})
    total_weight = sum(weights.values())
    normalized = (base / total_weight) + adjustment
    return round(normalized, 2), notes


def ranked_candidates(limit=None):
    queue = load_json(CONTENT_FILE, {"candidates": []})
    summary = load_json(GROWTH_SUMMARY, {})
    ranked = []
    for candidate in queue.get("candidates", []):
        score, notes = score_candidate(candidate, summary)
        ranked.append({**candidate, "priority_score": score, "planner_notes": notes})
    ranked.sort(key=lambda item: item["priority_score"], reverse=True)
    return ranked[:limit] if limit else ranked


def script_brief(candidate):
    return {
        "id": candidate["id"],
        "topic": candidate["topic"],
        "hook": candidate["hook"],
        "angle": candidate["angle"],
        "duration_target_seconds": candidate["duration_target_seconds"],
        "structure": [
            "0-2s: hook direct, no intro",
            "2-8s: promise and tension",
            "8-35s: technical explanation with one concrete example",
            "35-55s: visual demonstration or surprising implication",
            "55-70s: CTA and comment trigger",
        ],
        "visual_plan": candidate["visual_plan"],
        "cta": candidate["cta"],
        "caption": candidate["caption"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rank VulgaScience video candidates.")
    sub = parser.add_subparsers(dest="command", required=True)

    rank = sub.add_parser("rank")
    rank.add_argument("--limit", type=int)

    brief = sub.add_parser("brief")
    brief.add_argument("--id")

    args = parser.parse_args(argv)
    if args.command == "rank":
        ranked = ranked_candidates(args.limit)
        print(json.dumps(ranked, ensure_ascii=False, indent=2))
    elif args.command == "brief":
        ranked = ranked_candidates()
        selected = ranked[0] if not args.id else next(item for item in ranked if item["id"] == args.id)
        print(json.dumps(script_brief(selected), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
