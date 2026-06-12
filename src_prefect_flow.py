
import os
import time
import json
import logging
from dotenv import load_dotenv
from pathlib import Path

os.environ.setdefault("PREFECT_HOME", str(Path(os.getenv("STORAGE_ROOT", "./storage")) / "prefect"))

from prefect import flow, task, get_run_logger

load_dotenv()

FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL_MIN", "30")) * 60
SOURCES_FILE = Path(os.getenv("SOURCES_FILE", "config_sources.json"))

# Import pipeline functions
from src_pipeline import process_url

def logger_or_default():
    try:
        return get_run_logger()
    except Exception:
        return logging.getLogger(__name__)

@task
def discover_urls():
    logger = logger_or_default()
    # Very simple discovery: read config and build search URLs from channel ids
    try:
        cfg = json.loads(SOURCES_FILE.read_text())
    except Exception:
        cfg = {}
    urls = []
    y_channels = cfg.get("youtube_channels", [])
    for ch in y_channels:
        # For robustness, we use yt-dlp to list recent videos via channel URL
        urls.append(f"https://www.youtube.com/channel/{ch.get('id')}")
    logger.info(f"Discovered {len(urls)} seed URLs")
    return urls

@task
def schedule_process(urls):
    logger = logger_or_default()
    results = []
    for url in urls:
        try:
            res = process_url(url)
            results.append(res)
            logger.info(f"Processed {url} -> {res}")
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
    return results

@flow
def main_loop():
    logger = get_run_logger()
    logger.info("Starting pipeline loop")
    while True:
        urls = discover_urls()
        schedule_process(urls)
        logger.info(f"Sleeping for {FETCH_INTERVAL} seconds")
        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
