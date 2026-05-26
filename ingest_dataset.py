"""Batch-ingest SaaS pricing URLs into Crawlbase Cloud Storage (store=true)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Final
from urllib.parse import parse_qs, urlparse

import requests

CRAWLBASE_API_URL: Final = "https://api.crawlbase.com/"
DEFAULT_TIMEOUT_SECONDS: Final = 90
DEFAULT_MANIFEST: Final = Path("output/dataset-manifest.json")
DEFAULT_URLS: Final = Path("urls.saas-pricing.txt")


class IngestError(RuntimeError):
    pass


def load_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    if not urls:
        raise IngestError(f"No URLs found in {path}")
    return urls


def crawl_and_store(url: str, token: str, timeout: int) -> requests.Response:
    try:
        response = requests.get(
            CRAWLBASE_API_URL,
            params={
                "token": token,
                "url": url,
                "format": "md",
                "md_readability": "true",
                "store": "true",
            },
            timeout=timeout,
            headers={
                "Accept": "text/markdown",
                "Accept-Encoding": "gzip",
                "User-Agent": "crawlbase-research-dataset/1.0",
            },
        )
    except requests.RequestException as exc:
        raise IngestError(f"Request failed for {url}: {exc}") from exc
    return response


def extract_rid(response: requests.Response) -> str | None:
    rid = response.headers.get("rid")
    if rid:
        return rid
    storage_url = response.headers.get("storage_url")
    if not storage_url:
        return None
    params = parse_qs(urlparse(storage_url).query)
    values = params.get("rid", [])
    return values[0] if values else None


def is_stored(response: requests.Response) -> tuple[bool, str]:
    rid = extract_rid(response)
    pc_status = response.headers.get("pc_status", "")
    if not rid:
        return False, "missing_rid"
    if pc_status and pc_status != "200":
        return False, f"pc_status_{pc_status}"
    if response.status_code != 200:
        return False, f"http_{response.status_code}"
    return True, "ok"


def build_entry(url: str, response: requests.Response, stored: bool, reason: str) -> dict[str, object]:
    return {
        "url": url,
        "rid": extract_rid(response),
        "stored": stored,
        "reason": reason,
        "pc_status": response.headers.get("pc_status"),
        "resolved_url": response.headers.get("url"),
        "storage_url": response.headers.get("storage_url"),
        "crawled_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Store pricing pages in Crawlbase Cloud Storage.",
    )
    parser.add_argument(
        "--urls",
        type=Path,
        default=DEFAULT_URLS,
        help="Text file with one URL per line.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Output manifest JSON path.",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    token = os.getenv("CRAWLBASE_TOKEN")
    if not token:
        raise IngestError("Set CRAWLBASE_TOKEN before running ingest.")

    entries: list[dict[str, object]] = []
    for url in load_urls(args.urls):
        response = crawl_and_store(url, token, args.timeout)
        stored, reason = is_stored(response)
        entry = build_entry(url, response, stored, reason)
        entries.append(entry)
        label = "stored" if stored else "skipped"
        print(f"[{label}] {url} -> rid={entry.get('rid')} ({reason})")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(args.urls),
        "entry_count": len(entries),
        "stored_count": sum(1 for e in entries if e.get("stored")),
        "entries": entries,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nManifest written to {args.manifest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IngestError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
