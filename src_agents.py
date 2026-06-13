import argparse
import json
from pathlib import Path

from moviepy.editor import VideoFileClip

from src_approval_queue import list_reviews, print_reviews, save_review, submit_for_review


AGENTS = [
    {"id": "trend_scout", "mission": "Find science topics and trend signals before production."},
    {"id": "script_editor", "mission": "Write a clear French TikTok script with a strong hook."},
    {"id": "render_agent", "mission": "Create voiceover, subtitles, visuals, metadata, and caption."},
    {"id": "quality_gate", "mission": "Check duration, vertical format, audio, subtitles, and encoding."},
    {"id": "approval_agent", "mission": "Submit the candidate to human review and block publishing."},
    {"id": "publisher", "mission": "Publish only approved drafts, using TikTok API or safe fallback."},
]


def sidecar_paths(video_path):
    video_path = Path(video_path)
    paths = [video_path.with_suffix(".ass"), video_path.with_suffix(".srt"), video_path.with_suffix(".json")]
    return [path for path in paths if path.exists()]


def check_text_file(path):
    text = Path(path).read_bytes().decode("utf-8")
    return {
        "path": str(path),
        "unicode_escape_u00": text.count("\\u00"),
        "unicode_escape_u201": text.count("\\u201"),
        "literal_backslash_n": text.count("\\n") if Path(path).suffix.lower() != ".json" else 0,
        "mojibake_c3": text.count(chr(195)),
        "mojibake_a_circumflex": text.count(chr(226)),
        "replacement_char": text.count(chr(65533)),
    }


def quality_report(video_path):
    video_path = Path(video_path)
    report = {"agent": "quality_gate", "video_path": str(video_path), "ok": True, "checks": {}, "warnings": []}
    clip = VideoFileClip(str(video_path))
    try:
        width, height = clip.size
        report["checks"].update(
            {
                "duration_seconds": round(float(clip.duration), 2),
                "width": width,
                "height": height,
                "fps": float(clip.fps),
                "has_audio": clip.audio is not None,
                "vertical_9_16": height > width and abs((width / height) - (9 / 16)) < 0.02,
                "long_form_candidate": clip.duration >= 60.0,
            }
        )
    finally:
        clip.close()

    for key in ["has_audio", "vertical_9_16", "long_form_candidate"]:
        if not report["checks"].get(key):
            report["ok"] = False
            report["warnings"].append(f"Failed check: {key}")

    text_reports = [check_text_file(path) for path in sidecar_paths(video_path)]
    report["checks"]["sidecars"] = text_reports
    for item in text_reports:
        risky = sum(
            item[key]
            for key in [
                "unicode_escape_u00",
                "unicode_escape_u201",
                "literal_backslash_n",
                "mojibake_c3",
                "mojibake_a_circumflex",
                "replacement_char",
            ]
        )
        if risky:
            report["ok"] = False
            report["warnings"].append(f"Encoding issue in {item['path']}")
    return report


def review_video(video_path, metadata_path=None, caption=None):
    report = quality_report(video_path)
    if not report["ok"]:
        raise RuntimeError("Quality gate failed: " + json.dumps(report, ensure_ascii=False))
    review = submit_for_review(video_path, metadata_path, caption, source_agent="approval_agent")
    review["quality_report"] = report
    save_review(review)
    return review


def enqueue_latest(outbox="storage/outbox"):
    outbox = Path(outbox)
    videos = sorted(outbox.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not videos:
        raise FileNotFoundError(f"No mp4 found in {outbox}")
    video = videos[0]
    metadata = video.with_suffix(".json")
    return review_video(video, metadata if metadata.exists() else None)


def main(argv=None):
    parser = argparse.ArgumentParser(description="VulgaScience local agent workflow.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("agents")

    check = sub.add_parser("check")
    check.add_argument("--video", required=True)

    review = sub.add_parser("review")
    review.add_argument("--video", required=True)
    review.add_argument("--metadata")
    review.add_argument("--caption")

    latest = sub.add_parser("enqueue-latest")
    latest.add_argument("--outbox", default="storage/outbox")

    status = sub.add_parser("status")
    status.add_argument("--status")

    args = parser.parse_args(argv)
    if args.command == "agents":
        print(json.dumps(AGENTS, ensure_ascii=False, indent=2))
    elif args.command == "check":
        print(json.dumps(quality_report(args.video), ensure_ascii=False, indent=2))
    elif args.command == "review":
        print(json.dumps(review_video(args.video, args.metadata, args.caption), ensure_ascii=False, indent=2))
    elif args.command == "enqueue-latest":
        print(json.dumps(enqueue_latest(args.outbox), ensure_ascii=False, indent=2))
    elif args.command == "status":
        print_reviews(list_reviews(args.status))


if __name__ == "__main__":
    main()
