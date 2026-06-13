import argparse
import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
STORAGE_ROOT = Path(os.getenv("STORAGE_ROOT", "./storage"))
RAW_DIR = STORAGE_ROOT / "raw"
TRANS_DIR = STORAGE_ROOT / "transcripts"
OUTBOX = STORAGE_ROOT / "outbox"

RAW_DIR.mkdir(parents=True, exist_ok=True)
TRANS_DIR.mkdir(parents=True, exist_ok=True)
OUTBOX.mkdir(parents=True, exist_ok=True)


def is_url(value):
    parsed = urlparse(str(value))
    return parsed.scheme in {"http", "https"}


def unique_path(path):
    path = Path(path)
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def download_video(url, out_dir=RAW_DIR):
    before = {p.resolve() for p in out_dir.glob("*") if p.is_file()}
    out_template = str(out_dir / "%(id)s.%(ext)s")
    cmd = [sys.executable, "-m", "yt_dlp", "-f", "best", "-o", out_template, url]
    subprocess.run(cmd, check=True)
    after = [p for p in out_dir.glob("*") if p.is_file() and p.resolve() not in before]
    if after:
        return max(after, key=lambda p: p.stat().st_mtime)
    return max(out_dir.glob("*"), key=lambda p: p.stat().st_mtime)


def prepare_local_video(video_path, out_dir=RAW_DIR):
    source = Path(video_path)
    if not source.exists():
        raise FileNotFoundError(f"Video file not found: {source}")
    dest = unique_path(out_dir / source.name)
    if source.resolve() != dest.resolve():
        shutil.copy2(source, dest)
    return dest


def write_transcript(video_path, text, out_dir=TRANS_DIR):
    out_file = out_dir / f"{video_path.stem}.json"
    payload = {
        "segments": [
            {
                "start": 0.0,
                "end": 45.0,
                "text": text.strip() or "Transcript placeholder",
            }
        ]
    }
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_file


def transcribe(video_path, out_dir=TRANS_DIR, transcript_text=None):
    if transcript_text:
        return write_transcript(video_path, transcript_text, out_dir)

    out_file = out_dir / f"{video_path.stem}.json"
    try:
        cmd = ["whisperx", str(video_path), "--model", "small", "--output_dir", str(out_dir)]
        subprocess.run(cmd, check=True)
        if out_file.exists():
            return out_file
    except Exception:
        pass

    payload = {"segments": [{"start": 0.0, "end": 30.0, "text": "Transcript placeholder"}]}
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_file


def score_transcript(transcript_json):
    text = " ".join([s["text"] for s in transcript_json.get("segments", [])])
    score = min(100, max(0, int(len(text) / 10)))
    keywords = [
        "novel",
        "we show",
        "we propose",
        "new",
        "discover",
        "science",
        "recherche",
        "decouverte",
        "etude",
        "chercheurs",
        "cerveau",
        "espace",
        "energie",
        "ia",
        "intelligence artificielle",
    ]
    for kw in keywords:
        if kw in text.lower():
            score += 10
    return min(100, score)


def generate_script(segment_text):
    if not OPENAI_API_KEY:
        hook = "Tu ne vas pas y croire : "
        body = segment_text[:200]
        return f"{hook}{body}\nSuis-nous pour en savoir plus."

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    prompt = f"Resume et vulgarise en francais pour un TikTok de 45 secondes : {segment_text}"
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        json={
            "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
        },
        headers=headers,
        timeout=60,
    )
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    return "Erreur generation LLM. " + resp.text


def write_silent_wav(out_path, duration_s=3):
    sample_rate = 44100
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * sample_rate * duration_s)
    return out_path


def tts_generate(text, out_path):
    if not ELEVENLABS_KEY:
        duration_s = min(45, max(3, int(len(text) / 18)))
        return write_silent_wav(out_path, duration_s)

    headers = {
        "xi-api-key": ELEVENLABS_KEY,
        "Content-Type": "application/json",
    }
    resp = requests.post(
        "https://api.elevenlabs.io/v1/text-to-speech/default",
        headers=headers,
        json={"text": text},
        timeout=60,
    )
    if resp.status_code == 200:
        out_path.write_bytes(resp.content)
        return out_path
    return write_silent_wav(out_path)


def ffmpeg_executable():
    ffmpeg_bin = os.getenv("FFMPEG_BINARY", "ffmpeg")
    if ffmpeg_bin != "ffmpeg":
        return ffmpeg_bin
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ffmpeg_bin


def render_video(background_video, tts_wav, out_path):
    cmd = [
        ffmpeg_executable(),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(background_video),
        "-i",
        str(tts_wav),
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-shortest",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)
    return out_path


def publish(video_path, caption, metadata):
    dest = OUTBOX / video_path.name
    if video_path.resolve() != dest.resolve():
        video_path.replace(dest)

    meta_file = OUTBOX / f"{dest.stem}.json"
    meta_file.write_text(
        json.dumps({"caption": caption, "metadata": metadata}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    require_approval = os.getenv("REQUIRE_MANUAL_APPROVAL", "true").lower() in {"1", "true", "yes", "on"}
    if require_approval:
        from src_approval_queue import submit_for_review

        review = submit_for_review(dest, meta_file, caption=caption, source_agent="pipeline")
        review_mode = os.getenv("REVIEW_MODE", "local").lower()
        if review_mode in {"tiktok", "tiktok_inbox", "inbox"}:
            try:
                from src_approval_queue import stage_on_tiktok

                staged = stage_on_tiktok(review["draft_id"])
                return {
                    "status": staged["status"],
                    "path": str(dest),
                    "metadata_path": str(meta_file),
                    "draft_id": review["draft_id"],
                    "review_path": str(Path(review["video_path"]).parent / "review.json"),
                    "tiktok_stage_result": staged.get("tiktok_stage_result"),
                }
            except Exception as exc:
                return {
                    "status": "review_pending",
                    "path": str(dest),
                    "metadata_path": str(meta_file),
                    "draft_id": review["draft_id"],
                    "review_path": str(Path(review["video_path"]).parent / "review.json"),
                    "stage_error": str(exc),
                }
        return {
            "status": "review_pending",
            "path": str(dest),
            "metadata_path": str(meta_file),
            "draft_id": review["draft_id"],
            "review_path": str(Path(review["video_path"]).parent / "review.json"),
        }
    return {"status": "queued", "path": str(dest), "metadata_path": str(meta_file)}


def process_video_file(video_file, source_label=None, transcript_text=None, caption=None, force=False):
    print("Transcribing", video_file)
    transcript_file = transcribe(video_file, transcript_text=transcript_text)
    transcript_json = json.loads(Path(transcript_file).read_text(encoding="utf-8"))

    score = score_transcript(transcript_json)
    print("Score:", score)
    min_score = int(os.getenv("MIN_SCORE_TO_PROCESS", "40"))
    if score < min_score and not force:
        print("Score too low, archiving.")
        return {"status": "archived", "score": score, "min_score": min_score}

    segment_text = transcript_json["segments"][0]["text"]
    script = generate_script(segment_text)
    tts_path = RAW_DIR / f"{video_file.stem}_tts.wav"
    tts_generate(script, tts_path)

    out_video = unique_path(OUTBOX / f"{video_file.stem}_tiktok.mp4")
    render_video(video_file, tts_path, out_video)

    final_caption = caption or f"Vulgarisation auto - credit source {source_label or video_file.name}"
    result = publish(
        out_video,
        caption=final_caption,
        metadata={
            "score": score,
            "min_score": min_score,
            "forced": bool(force),
            "source": source_label or str(video_file),
            "transcript": str(transcript_file),
            "script": script,
        },
    )
    result.update({"score": score, "transcript": str(transcript_file)})
    return result


def process_source(source, transcript_text=None, caption=None, force=False):
    if is_url(source):
        print("Downloading", source)
        video_file = download_video(source)
    else:
        print("Preparing local video", source)
        video_file = prepare_local_video(source)

    return process_video_file(
        video_file,
        source_label=source,
        transcript_text=transcript_text,
        caption=caption,
        force=force,
    )


def process_url(url):
    return process_source(url)


def load_optional_text(value, file_path):
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prepare a short TikTok-ready video in storage/outbox.")
    parser.add_argument("source", help="Video URL or local video file")
    parser.add_argument("--transcript", help="Manual transcript text for MVP tests")
    parser.add_argument("--transcript-file", help="Path to a UTF-8 text transcript")
    parser.add_argument("--caption", help="Caption to store next to the rendered video")
    parser.add_argument("--force", action="store_true", help="Render even when the score is below MIN_SCORE_TO_PROCESS")
    args = parser.parse_args(argv)

    transcript_text = load_optional_text(args.transcript, args.transcript_file)
    result = process_source(args.source, transcript_text=transcript_text, caption=args.caption, force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
