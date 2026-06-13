"""
TikTok Content Posting API integration.

Default safe path:
- Upload the video to the creator's TikTok inbox with the `video.upload` scope.
- The creator opens TikTok, adds/chooses music, edits if needed, and posts manually.

Direct posting is kept as an explicit opt-in path and requires the `video.publish`
scope plus an audited TikTok app for public visibility.
"""

import argparse
import json
import math
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
TIKTOK_REFRESH_TOKEN = os.getenv("TIKTOK_REFRESH_TOKEN")

STORAGE = Path(os.getenv("STORAGE_ROOT", "./storage"))
OUTBOX = STORAGE / "outbox"
PUBLISHED = STORAGE / "published"
STAGED = STORAGE / "staged_tiktok"
OUTBOX.mkdir(parents=True, exist_ok=True)
PUBLISHED.mkdir(parents=True, exist_ok=True)
STAGED.mkdir(parents=True, exist_ok=True)

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
CREATOR_INFO_URL = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
INBOX_VIDEO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
DIRECT_VIDEO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

DEFAULT_CHUNK_SIZE = int(os.getenv("TIKTOK_UPLOAD_CHUNK_SIZE", str(8 * 1024 * 1024)))


def require_credentials(require_refresh=False):
    if not (TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET):
        raise RuntimeError("TikTok client key/secret are missing")
    if require_refresh and not TIKTOK_REFRESH_TOKEN:
        raise RuntimeError("TikTok refresh token is missing")


def refresh_access_token():
    require_credentials(require_refresh=True)
    resp = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache"},
        data={
            "client_key": TIKTOK_CLIENT_KEY,
            "client_secret": TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": TIKTOK_REFRESH_TOKEN,
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError("Failed to refresh TikTok token: " + resp.text)
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("TikTok refresh response did not include access_token")
    return data


def get_access_token():
    if TIKTOK_ACCESS_TOKEN:
        return TIKTOK_ACCESS_TOKEN
    return refresh_access_token()["access_token"]


def auth_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }


def parse_tiktok_response(resp, context):
    try:
        payload = resp.json()
    except Exception:
        payload = {"raw": resp.text}
    if resp.status_code >= 400:
        raise RuntimeError(f"{context} failed ({resp.status_code}): {json.dumps(payload, ensure_ascii=False)}")
    error = payload.get("error") or {}
    if error.get("code") not in (None, "ok"):
        raise RuntimeError(f"{context} failed: {json.dumps(payload, ensure_ascii=False)}")
    return payload.get("data", payload)


def query_creator_info(access_token=None):
    access_token = access_token or get_access_token()
    resp = requests.post(CREATOR_INFO_URL, headers=auth_headers(access_token), timeout=30)
    return parse_tiktok_response(resp, "Query creator info")


def chunk_plan(video_path, chunk_size=DEFAULT_CHUNK_SIZE):
    video_size = Path(video_path).stat().st_size
    chunk_size = min(chunk_size, video_size) if video_size else chunk_size
    total_chunk_count = max(1, math.ceil(video_size / chunk_size))
    return video_size, chunk_size, total_chunk_count


def init_inbox_upload(access_token, video_path):
    video_size, chunk_size, total_chunk_count = chunk_plan(video_path)
    payload = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunk_count,
        }
    }
    resp = requests.post(INBOX_VIDEO_INIT_URL, headers=auth_headers(access_token), json=payload, timeout=30)
    data = parse_tiktok_response(resp, "Initialize TikTok inbox upload")
    if not data.get("upload_url") or not data.get("publish_id"):
        raise RuntimeError("TikTok inbox upload response missing upload_url or publish_id")
    return data, chunk_size


def init_direct_post(access_token, video_path, caption, privacy_level="SELF_ONLY"):
    video_size, chunk_size, total_chunk_count = chunk_plan(video_path)
    payload = {
        "post_info": {
            "title": caption[:2200],
            "privacy_level": privacy_level,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunk_count,
        },
    }
    resp = requests.post(DIRECT_VIDEO_INIT_URL, headers=auth_headers(access_token), json=payload, timeout=30)
    data = parse_tiktok_response(resp, "Initialize TikTok direct post")
    if not data.get("upload_url") or not data.get("publish_id"):
        raise RuntimeError("TikTok direct post response missing upload_url or publish_id")
    return data, chunk_size


def upload_chunks(upload_url, video_path, chunk_size):
    video_path = Path(video_path)
    video_size = video_path.stat().st_size
    with video_path.open("rb") as fh:
        start = 0
        while start < video_size:
            data = fh.read(chunk_size)
            end = start + len(data) - 1
            headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(len(data)),
                "Content-Range": f"bytes {start}-{end}/{video_size}",
            }
            resp = requests.put(upload_url, headers=headers, data=data, timeout=120)
            if resp.status_code >= 400:
                raise RuntimeError(f"TikTok upload chunk failed ({resp.status_code}): {resp.text}")
            start = end + 1


def fetch_post_status(publish_id, access_token=None):
    access_token = access_token or get_access_token()
    resp = requests.post(
        STATUS_URL,
        headers=auth_headers(access_token),
        json={"publish_id": publish_id},
        timeout=30,
    )
    return parse_tiktok_response(resp, "Fetch TikTok post status")


def upload_to_tiktok_inbox(video_path, caption=None):
    access_token = get_access_token()
    video_path = Path(video_path)
    data, chunk_size = init_inbox_upload(access_token, video_path)
    upload_chunks(data["upload_url"], video_path, chunk_size)
    result = {
        "status": "uploaded_to_tiktok_inbox",
        "publish_id": data["publish_id"],
        "video_path": str(video_path),
        "caption": caption,
        "next_step": "Open TikTok inbox/notification, add a trending sound if useful, then publish manually.",
    }
    (STAGED / f"{video_path.stem}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def direct_post_video(video_path, caption, privacy_level="SELF_ONLY"):
    access_token = get_access_token()
    video_path = Path(video_path)
    data, chunk_size = init_direct_post(access_token, video_path, caption, privacy_level)
    upload_chunks(data["upload_url"], video_path, chunk_size)
    result = {
        "status": "direct_post_initialized",
        "publish_id": data["publish_id"],
        "video_path": str(video_path),
        "caption": caption,
        "privacy_level": privacy_level,
    }
    return result


def publish_from_path(video_path, caption, hashtags=None):
    extra = " ".join("#" + tag.lstrip("#") for tag in (hashtags or []))
    caption = (caption + " " + extra).strip()
    mode = os.getenv("TIKTOK_POST_MODE", "inbox").lower()
    if mode == "direct":
        privacy = os.getenv("TIKTOK_PRIVACY_LEVEL", "SELF_ONLY")
        return direct_post_video(video_path, caption, privacy_level=privacy)
    return upload_to_tiktok_inbox(video_path, caption)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Upload videos with TikTok Content Posting API.")
    sub = parser.add_subparsers(dest="command", required=True)

    info = sub.add_parser("creator-info")
    info.set_defaults(fn=lambda args: query_creator_info())

    inbox = sub.add_parser("upload-inbox")
    inbox.add_argument("--video", required=True)
    inbox.add_argument("--caption", default="")

    direct = sub.add_parser("direct-post")
    direct.add_argument("--video", required=True)
    direct.add_argument("--caption", required=True)
    direct.add_argument("--privacy-level", default="SELF_ONLY")

    status = sub.add_parser("status")
    status.add_argument("publish_id")

    args = parser.parse_args(argv)
    if args.command == "creator-info":
        result = query_creator_info()
    elif args.command == "upload-inbox":
        result = upload_to_tiktok_inbox(args.video, args.caption)
    elif args.command == "direct-post":
        result = direct_post_video(args.video, args.caption, args.privacy_level)
    elif args.command == "status":
        result = fetch_post_status(args.publish_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
