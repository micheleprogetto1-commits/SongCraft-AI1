#!/usr/bin/env python3
"""
Download royalty-free MP3 audio from Pixabay into audio_assets/.

Features:
- Respects a maximum download count
- Skips duplicate files by URL and by content hash
- Retries transient network/API failures
- Adds a small delay between downloads to reduce throttling risk
- Skips files larger than GitHub's 100 MB per-file limit

Environment variables:
- PIXABAY_API_KEY: required
- PIXABAY_QUERY: optional, default "music"
- PIXABAY_MAX_FILES: optional, default 1000
- PIXABAY_PER_PAGE: optional, default 200
- PIXABAY_DELAY_SECONDS: optional, default 1.5
- PIXABAY_OUTPUT_DIR: optional, default "audio_assets"
"""

from __future__ import annotations

import hashlib
import os
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests


PIXABAY_API_URL = "https://pixabay.com/api/music/"
MAX_GITHUB_FILE_BYTES = 100 * 1024 * 1024
DEFAULT_QUERY = "music"
DEFAULT_MAX_FILES = 1000
DEFAULT_PER_PAGE = 200
DEFAULT_DELAY_SECONDS = 1.5
REQUEST_TIMEOUT = 30
MAX_RETRIES = 5


@dataclass(frozen=True)
class AudioItem:
    id: int
    tags: str
    preview_url: str
    download_url: str


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


def sanitize_filename(value: str) -> str:
    keep = []
    for ch in value:
        if ch.isalnum() or ch in {"-", "_", "."}:
            keep.append(ch)
        else:
            keep.append("_")
    name = "".join(keep).strip("._")
    return name or "audio"


def api_get(session: requests.Session, params: dict) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(PIXABAY_API_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == MAX_RETRIES:
                raise
            sleep_for = min(2**attempt, 20) + random.uniform(0, 1)
            print(f"[warn] Pixabay API error (attempt {attempt}/{MAX_RETRIES}): {exc}. Retrying in {sleep_for:.1f}s")
            time.sleep(sleep_for)
    raise RuntimeError(f"Pixabay API failed: {last_error}")


def download_stream(session: requests.Session, url: str) -> Iterable[bytes]:
    with session.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=1024 * 64):
            if chunk:
                yield chunk


def existing_hashes(output_dir: Path) -> set[str]:
    hashes: set[str] = set()
    for file in output_dir.glob("*.mp3"):
        try:
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            hashes.add(digest)
        except OSError:
            continue
    return hashes


def load_existing_urls(index_file: Path) -> set[str]:
    if not index_file.exists():
        return set()
    return {line.strip() for line in index_file.read_text(encoding="utf-8").splitlines() if line.strip()}


def append_url(index_file: Path, url: str) -> None:
    with index_file.open("a", encoding="utf-8") as fh:
        fh.write(url + "\n")


def fetch_items(session: requests.Session, api_key: str, query: str, per_page: int, page: int) -> list[AudioItem]:
    payload = {
        "key": api_key,
        "q": query,
        "per_page": per_page,
        "page": page,
        "safesearch": "true",
    }
    data = api_get(session, payload)
    items = []
    for hit in data.get("hits", []):
        preview_url = hit.get("previewURL") or hit.get("preview_url")
        download_url = hit.get("audio_url") or hit.get("downloadURL") or hit.get("download_url")
        if not preview_url or not download_url:
            continue
        items.append(
            AudioItem(
                id=int(hit.get("id", 0)),
                tags=str(hit.get("tags", "")).strip(),
                preview_url=str(preview_url),
                download_url=str(download_url),
            )
        )
    return items


def main() -> int:
    api_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not api_key:
        print("PIXABAY_API_KEY is required.", file=sys.stderr)
        return 1

    query = os.environ.get("PIXABAY_QUERY", DEFAULT_QUERY).strip() or DEFAULT_QUERY
    max_files = env_int("PIXABAY_MAX_FILES", DEFAULT_MAX_FILES)
    per_page = max(1, min(env_int("PIXABAY_PER_PAGE", DEFAULT_PER_PAGE), 200))
    delay_seconds = max(0.0, env_float("PIXABAY_DELAY_SECONDS", DEFAULT_DELAY_SECONDS))
    output_dir = Path(os.environ.get("PIXABAY_OUTPUT_DIR", "audio_assets"))
    output_dir.mkdir(parents=True, exist_ok=True)

    index_file = output_dir / ".downloaded_urls.txt"
    seen_urls = load_existing_urls(index_file)
    seen_hashes = existing_hashes(output_dir)

    session = requests.Session()
    session.headers.update({"User-Agent": "SongCraft-AI-Audio-Downloader/1.0"})

    downloaded = 0
    page = 1
    total_seen_this_run = 0

    while downloaded < max_files:
        items = fetch_items(session, api_key, query, per_page, page)
        if not items:
            break

        for item in items:
            if downloaded >= max_files:
                break

            if item.download_url in seen_urls:
                continue

            safe_tag = sanitize_filename(item.tags.split(",")[0] if item.tags else f"pixabay_{item.id}")
            target_file = output_dir / f"{item.id}_{safe_tag}.mp3"
            if target_file.exists():
                seen_urls.add(item.download_url)
                continue

            try:
                head = session.head(item.download_url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
                if head.headers.get("Content-Length"):
                    size = int(head.headers["Content-Length"])
                    if size > MAX_GITHUB_FILE_BYTES:
                        print(f"[skip] {item.id} exceeds 100MB ({size} bytes)")
                        continue

                hasher = hashlib.sha256()
                temp_file = target_file.with_suffix(".mp3.part")
                with temp_file.open("wb") as fh:
                    for chunk in download_stream(session, item.download_url):
                        fh.write(chunk)
                        hasher.update(chunk)

                file_size = temp_file.stat().st_size
                if file_size > MAX_GITHUB_FILE_BYTES:
                    print(f"[skip] {item.id} exceeds 100MB after download ({file_size} bytes)")
                    temp_file.unlink(missing_ok=True)
                    continue

                file_hash = hasher.hexdigest()
                if file_hash in seen_hashes:
                    print(f"[skip] duplicate content for {item.id}")
                    temp_file.unlink(missing_ok=True)
                    seen_urls.add(item.download_url)
                    continue

                temp_file.replace(target_file)
                seen_urls.add(item.download_url)
                seen_hashes.add(file_hash)
                append_url(index_file, item.download_url)
                downloaded += 1
                total_seen_this_run += 1
                print(f"[ok] downloaded {target_file.name} ({downloaded}/{max_files})")
                time.sleep(delay_seconds)
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] failed to download {item.id}: {exc}")
                continue

        page += 1

    print(f"Completed. New files downloaded: {downloaded}. Items processed: {total_seen_this_run}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
