import argparse
import json
import os
from pathlib import Path

from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
STORAGE = Path(os.getenv("STORAGE_ROOT", "./storage"))
EXPECTED_REDIRECT = "https://vulgascience.github.io/vulgascience-legal/callback.html"


def file_check(path):
    path = Path(path)
    return {
        "path": str(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else 0,
    }


def env_status():
    cfg = dotenv_values(ROOT / ".env")
    keys = [
        "TIKTOK_CLIENT_KEY",
        "TIKTOK_CLIENT_SECRET",
        "TIKTOK_ACCESS_TOKEN",
        "TIKTOK_REFRESH_TOKEN",
        "TIKTOK_SCOPES",
        "TIKTOK_REDIRECT_URI",
        "REVIEW_MODE",
    ]
    status = {key: bool(cfg.get(key)) for key in keys}
    scopes_value = cfg.get("TIKTOK_SCOPES", "video.upload,user.info.basic")
    redirect_value = cfg.get("TIKTOK_REDIRECT_URI", EXPECTED_REDIRECT)
    scopes = [scope.strip() for scope in scopes_value.split(",") if scope.strip()]
    status["scopes"] = scopes
    status["has_video_upload"] = "video.upload" in scopes
    status["redirect_uri"] = redirect_value
    status["redirect_matches_expected"] = redirect_value == EXPECTED_REDIRECT
    status["review_mode"] = cfg.get("REVIEW_MODE", "local")
    return status


def review_drafts():
    review_dir = STORAGE / "review"
    drafts = []
    for path in sorted(review_dir.glob("*/review.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        video_path = ROOT / data.get("video_path", "")
        drafts.append(
            {
                "draft_id": data.get("draft_id"),
                "status": data.get("status"),
                "video_path": data.get("video_path"),
                "video_exists": video_path.exists(),
                "caption": data.get("caption"),
            }
        )
    return drafts


def build_report():
    env = env_status()
    docs = [
        file_check(DOCS / "index.html"),
        file_check(DOCS / "callback.html"),
        file_check(DOCS / "terms.html"),
        file_check(DOCS / "privacy.html"),
    ]
    drafts = review_drafts()

    blockers = []
    if not all(item["exists"] for item in docs):
        blockers.append("Missing public docs page")
    if not env["TIKTOK_CLIENT_KEY"] or not env["TIKTOK_CLIENT_SECRET"]:
        blockers.append("TikTok client key/secret missing")
    if not env["has_video_upload"]:
        blockers.append("TIKTOK_SCOPES must include video.upload")
    if env["TIKTOK_REDIRECT_URI"] and not env["redirect_matches_expected"]:
        blockers.append("TikTok redirect URI differs from expected GitHub Pages callback")
    if not drafts:
        blockers.append("No review draft available")

    ready_for_oauth = not any(
        item in blockers
        for item in [
            "Missing public docs page",
            "TikTok client key/secret missing",
            "TIKTOK_SCOPES must include video.upload",
        ]
    )
    ready_for_stage = ready_for_oauth and env["TIKTOK_ACCESS_TOKEN"] and env["TIKTOK_REFRESH_TOKEN"] and bool(drafts)

    return {
        "ok": not blockers,
        "ready_for_oauth": ready_for_oauth,
        "ready_for_tiktok_inbox_stage": ready_for_stage,
        "blockers": blockers,
        "docs": docs,
        "env": env,
        "drafts": drafts,
        "next_actions": next_actions(blockers, env, drafts),
    }


def next_actions(blockers, env, drafts):
    actions = []
    if "Missing public docs page" not in blockers:
        actions.append("Push docs/index.html and docs/callback.html to GitHub Pages.")
    if not env["TIKTOK_CLIENT_KEY"] or not env["TIKTOK_CLIENT_SECRET"]:
        actions.append("After approval, add TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET to .env.")
    if not env["TIKTOK_ACCESS_TOKEN"] or not env["TIKTOK_REFRESH_TOKEN"]:
        actions.append("Run: python src_tiktok_oauth.py auth-url --open, then exchange the callback code.")
    if drafts:
        actions.append(f"Stage latest draft: python src_approval_queue.py stage {drafts[-1]['draft_id']}")
    else:
        actions.append("Create or enqueue a video draft before staging.")
    return actions


def print_human(report):
    print("VulgaScience launch check")
    print("-------------------------")
    print("Ready for OAuth:", "yes" if report["ready_for_oauth"] else "no")
    print("Ready for TikTok inbox staging:", "yes" if report["ready_for_tiktok_inbox_stage"] else "no")
    if report["blockers"]:
        print("\nBlockers:")
        for item in report["blockers"]:
            print(f"- {item}")
    print("\nNext actions:")
    for item in report["next_actions"]:
        print(f"- {item}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check readiness for TikTok approval/upload.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
