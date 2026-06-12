
import os
import json
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

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

# Simple helper: download via yt-dlp
def download_video(url, out_dir=RAW_DIR):
    out_template = str(out_dir / "%(id)s.%(ext)s")
    cmd = ["yt-dlp", "-f", "best", "-o", out_template, url]
    subprocess.run(cmd, check=True)
    # find downloaded file (simple heuristic)
    return list(out_dir.glob("*"))[-1]

# Transcription (calls whisperx or OpenAI Whisper)
def transcribe(video_path, out_dir=TRANS_DIR):
    # Attempt whisperx (local) first
    out_file = out_dir / (video_path.stem + ".json")
    try:
        cmd = ["whisperx", str(video_path), "--model", "small", "--output_dir", str(out_dir)]
        subprocess.run(cmd, check=True)
        # assume whisperx produced .json in out_dir
        if out_file.exists():
            return out_file
    except Exception:
        pass
    # Fallback: call OpenAI Whisper API (pseudo)
    # TODO: implement API call to OpenAI if available
    # For now, create dummy transcript
    with open(out_file, "w") as f:
        json.dump({"segments": [{"start": 0.0, "end": 30.0, "text": "Transcript placeholder"}]}, f)
    return out_file

# Basic scoring function
def score_transcript(transcript_json):
    # Very simple scoring: length + keyword boost
    text = " ".join([s["text"] for s in transcript_json.get("segments", [])])
    score = min(100, max(0, int(len(text) / 10)))
    keywords = ["novel", "we show", "we propose", "new", "discover"]
    for kw in keywords:
        if kw in text.lower():
            score += 10
    return score

# Generate script via OpenAI (simplified)
def generate_script(segment_text):
    if not OPENAI_API_KEY:
        # local fallback: simple template
        hook = "Tu ne vas pas y croire : "
        body = segment_text[:200]
        script = f"{hook}{body}\nSuis-nous pour en savoir plus."
        return script
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    prompt = f"Résume et vulgarise en FR (45s) : {segment_text}"
    # Minimal OpenAI call (pseudo)
    resp = requests.post("https://api.openai.com/v1/chat/completions", json={
        "model":"gpt-4o",
        "messages":[{"role":"user","content":prompt}],
        "max_tokens":400
    }, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    else:
        return "Erreur génération LLM. " + resp.text

# TTS (ElevenLabs) minimal
def tts_generate(text, out_path):
    if not ELEVENLABS_KEY:
        # Fallback: use eSpeak (if installed) or create empty wav
        out_path.write_bytes(b"")  # placeholder
        return out_path
    headers = {
        "xi-api-key": ELEVENLABS_KEY,
        "Content-Type": "application/json"
    }
    # simplified call: user must adapt voice id
    resp = requests.post("https://api.elevenlabs.io/v1/text-to-speech/default", headers=headers, json={
        "text": text
    })
    if resp.status_code == 200:
        out_path.write_bytes(resp.content)
    else:
        out_path.write_bytes(b"")
    return out_path

# Rendering: combine background + tts via ffmpeg
def render_video(background_video, tts_wav, out_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", str(background_video),
        "-i", str(tts_wav),
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        str(out_path)
    ]
    subprocess.run(cmd, check=True)
    return out_path

# Publish stub (writes metadata to outbox or calls TikTok API)
def publish(video_path, caption, metadata):
    # If TikTok credentials present, call API (not implemented here)
    # Otherwise move to outbox for manual upload
    dest = OUTBOX / (video_path.name)
    video_path.replace(dest)
    meta_file = OUTBOX / (video_path.stem + ".json")
    with open(meta_file, "w") as f:
        json.dump({"caption": caption, "metadata": metadata}, f, ensure_ascii=False, indent=2)
    return {"status":"queued", "path": str(dest)}

# High-level pipeline for a single URL
def process_url(url):
    print("Downloading", url)
    video_file = download_video(url)
    print("Transcribing", video_file)
    transcript_file = transcribe(video_file)
    with open(transcript_file, "r") as f:
        transcript_json = json.load(f)
    score = score_transcript(transcript_json)
    print("Score:", score)
    if score < int(os.getenv("MIN_SCORE_TO_PROCESS", "40")):
        print("Score too low, archiving.")
        return {"status":"archived", "score": score}
    # take first segment for demo
    segment_text = transcript_json["segments"][0]["text"]
    script = generate_script(segment_text)
    tts_path = RAW_DIR / (video_file.stem + "_tts.wav")
    tts_generate(script, tts_path)
    bg_video = video_file  # for MVP use same video as background (later create template)
    out_video = OUTBOX / (video_file.stem + "_tiktok.mp4")
    render_video(bg_video, tts_path, out_video)
    publish(out_video, caption="Vulgarisation auto — crédit source " + url, metadata={"score": score})
    return {"status":"published_queue", "score": score}

if __name__ == "__main__":
    # Basic loop for manual testing
    example_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # replace
    print(process_url(example_url))
