import argparse
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

STORAGE = Path(os.getenv("STORAGE_ROOT", "./storage"))
REVIEW_DIR = STORAGE / "review"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def slugify(value):
    value = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(value)).strip("-")
    return value[:80] or "draft"


def load_json(path, default=None):
    if not path:
        return default if default is not None else {}
    path = Path(path)
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def review_path(draft_id):
    return REVIEW_DIR / draft_id / "review.json"


def load_review(draft_id):
    path = review_path(draft_id)
    if not path.exists():
        raise FileNotFoundError(f"Unknown draft: {draft_id}")
    return load_json(path)


def save_review(review):
    path = review_path(review["draft_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, review)
    return path


def sidecar_candidates(video_path, metadata_path=None):
    candidates = []
    for suffix in [".ass", ".srt", ".json"]:
        sidecar = video_path.with_suffix(suffix)
        if sidecar.exists():
            candidates.append(sidecar)
    if metadata_path:
        metadata_path = Path(metadata_path)
        if metadata_path.exists() and metadata_path not in candidates:
            candidates.append(metadata_path)
    return candidates


def pick_caption(metadata, caption=None):
    if caption:
        return caption
    for key in ["caption_recommended", "caption"]:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    nested = metadata.get("metadata")
    if isinstance(nested, dict):
        return pick_caption(nested)
    return "Science claire, en 60 secondes. #science #vulgarisation"


def submit_for_review(video_path, metadata_path=None, caption=None, source_agent="manual"):
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    metadata = load_json(metadata_path, default={})
    draft_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slugify(video_path.stem)}"
    draft_dir = REVIEW_DIR / draft_id
    draft_dir.mkdir(parents=True, exist_ok=False)

    review_video = draft_dir / video_path.name
    shutil.copy2(video_path, review_video)

    copied_sidecars = []
    for sidecar in sidecar_candidates(video_path, metadata_path):
        dest = draft_dir / sidecar.name
        if sidecar.resolve() != dest.resolve():
            shutil.copy2(sidecar, dest)
        copied_sidecars.append(str(dest))

    review = {
        "draft_id": draft_id,
        "status": "pending",
        "created_at": utc_now(),
        "source_agent": source_agent,
        "video_path": str(review_video),
        "caption": pick_caption(metadata, caption),
        "metadata_path": str(draft_dir / Path(metadata_path).name) if metadata_path else None,
        "sidecars": copied_sidecars,
        "metadata": metadata,
        "history": [{"at": utc_now(), "event": "submitted_for_review", "agent": source_agent}],
    }
    save_review(review)
    return review


def list_reviews(status=None):
    reviews = []
    for path in sorted(REVIEW_DIR.glob("*/review.json")):
        try:
            review = load_json(path)
        except Exception:
            continue
        if status and review.get("status") != status:
            continue
        reviews.append(review)
    return reviews


def approve(draft_id, approver="human"):
    review = load_review(draft_id)
    if review.get("status") == "published":
        raise RuntimeError("Draft is already published")
    review["status"] = "approved"
    review["approved_at"] = utc_now()
    review["history"].append({"at": utc_now(), "event": "approved", "agent": approver})
    save_review(review)
    return review


def reject(draft_id, reason="", approver="human"):
    review = load_review(draft_id)
    if review.get("status") == "published":
        raise RuntimeError("Draft is already published")
    review["status"] = "rejected"
    review["rejected_at"] = utc_now()
    review["rejection_reason"] = reason
    review["history"].append({"at": utc_now(), "event": "rejected", "agent": approver, "reason": reason})
    save_review(review)
    return review


def publish_approved(draft_id, dry_run=False):
    review = load_review(draft_id)
    if review.get("status") != "approved":
        raise RuntimeError(f"Draft must be approved before publish, got {review.get('status')}")

    if dry_run:
        result = {"status": "dry_run", "path": review["video_path"], "caption": review["caption"]}
    else:
        from src_tiktok_publisher import publish_from_path

        result = publish_from_path(Path(review["video_path"]), review["caption"])

    review["publish_result"] = result
    review["history"].append({"at": utc_now(), "event": "publish_attempted", "result": result})
    if result.get("status") == "published":
        review["status"] = "published"
        review["published_at"] = utc_now()
    elif result.get("status") != "dry_run":
        review["status"] = "publish_pending"
    save_review(review)
    return review


def stage_on_tiktok(draft_id, dry_run=False):
    review = load_review(draft_id)
    if review.get("status") not in {"pending", "approved", "publish_pending"}:
        raise RuntimeError(f"Draft cannot be staged from status {review.get('status')}")

    if dry_run:
        result = {
            "status": "dry_run",
            "path": review["video_path"],
            "caption": review["caption"],
            "next_step": "Would upload to TikTok inbox for final review in the TikTok app.",
        }
        return {**review, "tiktok_stage_result": result}
    else:
        from src_tiktok_publisher import upload_to_tiktok_inbox

        result = upload_to_tiktok_inbox(Path(review["video_path"]), review["caption"])

    review["tiktok_stage_result"] = result
    review["history"].append({"at": utc_now(), "event": "staged_on_tiktok", "result": result})
    if result.get("status") == "uploaded_to_tiktok_inbox":
        review["status"] = "staged_on_tiktok"
        review["staged_at"] = utc_now()
    save_review(review)
    return review


def print_reviews(reviews):
    if not reviews:
        print("No drafts.")
        return
    for review in reviews:
        print(f"{review['draft_id']} | {review.get('status')} | {review.get('caption', '')[:90]}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Human approval queue for TikTok videos.")
    sub = parser.add_subparsers(dest="command", required=True)

    submit = sub.add_parser("submit")
    submit.add_argument("--video", required=True)
    submit.add_argument("--metadata")
    submit.add_argument("--caption")
    submit.add_argument("--agent", default="manual")

    ls = sub.add_parser("list")
    ls.add_argument("--status")

    approve_cmd = sub.add_parser("approve")
    approve_cmd.add_argument("draft_id")

    reject_cmd = sub.add_parser("reject")
    reject_cmd.add_argument("draft_id")
    reject_cmd.add_argument("--reason", default="")

    publish_cmd = sub.add_parser("publish")
    publish_cmd.add_argument("draft_id")
    publish_cmd.add_argument("--dry-run", action="store_true")

    stage_cmd = sub.add_parser("stage")
    stage_cmd.add_argument("draft_id")
    stage_cmd.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "submit":
        review = submit_for_review(args.video, args.metadata, args.caption, args.agent)
        print(json.dumps(review, ensure_ascii=False, indent=2))
    elif args.command == "list":
        print_reviews(list_reviews(args.status))
    elif args.command == "approve":
        print(json.dumps(approve(args.draft_id), ensure_ascii=False, indent=2))
    elif args.command == "reject":
        print(json.dumps(reject(args.draft_id, args.reason), ensure_ascii=False, indent=2))
    elif args.command == "publish":
        print(json.dumps(publish_approved(args.draft_id, dry_run=args.dry_run), ensure_ascii=False, indent=2))
    elif args.command == "stage":
        print(json.dumps(stage_on_tiktok(args.draft_id, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
