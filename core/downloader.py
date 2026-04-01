# ============================================================
#  FreedomForge AI — core/downloader.py
#  Unified download manager — resumable, retry, progress
# ============================================================

import os
import queue
import threading
import time
from typing import Callable, Optional
from core import logger
from utils.paths import MODELS_DIR

MAX_RETRIES    = 3
RETRY_DELAY    = 2   # seconds, doubles each retry
CHUNK_SIZE     = 65536


def download_model(
    url:         str,
    filename:    str,
    on_progress: Callable[[int, int], None] = None,
    on_complete: Callable[[], None] = None,
    on_error:    Callable[[str], None] = None,
) -> threading.Thread:
    """
    Download a model file with resume support and retry logic.
    Runs in a background thread.
    Returns the thread so caller can join if needed.
    """
    t = threading.Thread(
        target=_download_worker,
        args=(url, filename, on_progress, on_complete, on_error),
        daemon=True,
    )
    t.start()
    return t


def _download_worker(url, filename, on_progress, on_complete, on_error):
    try:
        import requests
    except ImportError:
        if on_error:
            on_error("requests library not installed")
        return

    os.makedirs(str(MODELS_DIR), exist_ok=True)
    dest = os.path.join(str(MODELS_DIR), filename)
    tmp  = dest + ".part"

    attempt = 0
    delay   = RETRY_DELAY

    while attempt < MAX_RETRIES:
        attempt += 1
        try:
            # Resume support — check existing partial file
            resume_pos = 0
            headers    = {}
            if os.path.exists(tmp):
                resume_pos = os.path.getsize(tmp)
                if resume_pos > 0:
                    headers["Range"] = f"bytes={resume_pos}-"
                    logger.info(f"Resuming download from byte {resume_pos}")

            r = requests.get(url, stream=True, timeout=60, headers=headers)

            # 416 = range not satisfiable — server doesn't support resume
            if r.status_code == 416:
                os.remove(tmp)
                resume_pos = 0
                r = requests.get(url, stream=True, timeout=60)

            r.raise_for_status()

            total = int(r.headers.get("content-length", 0))
            if resume_pos and total:
                total += resume_pos

            done = resume_pos
            mode = "ab" if resume_pos else "wb"

            with open(tmp, mode) as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        if on_progress and total:
                            on_progress(done, total)

            # Success — rename to final filename
            if os.path.exists(dest):
                os.remove(dest)
            os.rename(tmp, dest)
            logger.info(f"Download complete: {filename}")

            if on_complete:
                on_complete()
            return

        except Exception as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt >= MAX_RETRIES:
                # Clean up partial file on final failure
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass
                if on_error:
                    on_error(f"Download failed after {MAX_RETRIES} attempts: {e}")
                return
            logger.info(f"Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2


def get_partial_size(filename: str) -> int:
    """Return size of partial download file in bytes, or 0."""
    tmp = os.path.join(str(MODELS_DIR), filename + ".part")
    if os.path.exists(tmp):
        return os.path.getsize(tmp)
    return 0


def cancel_partial(filename: str) -> None:
    """Delete any partial download file."""
    tmp = os.path.join(str(MODELS_DIR), filename + ".part")
    if os.path.exists(tmp):
        try:
            os.remove(tmp)
        except Exception:
            pass
