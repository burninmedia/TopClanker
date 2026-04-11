"""
Scraper for the LMSYS Chatbot Arena leaderboard.

Primary path: fetch the most recent `leaderboard_table_*.csv` file published
              under the HF Space repo.
Fallback:     scrape the HTML table from https://lmarena.ai/.

Output file: data/raw/lmsys_arena.json

Only one benchmark key is emitted: `lmsys_elo`, with `score` = Arena Elo and
the battle count stored alongside under `votes`.
"""

from __future__ import annotations

import csv
import io
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from rich.console import Console

SOURCE_NAME = "lmsys_arena"
BENCHMARK_KEY = "lmsys_elo"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "lmsys_arena.json"

SPACE_TREE_API = "https://huggingface.co/api/spaces/lmsys/chatbot-arena-leaderboard/tree/main"
SPACE_FILE_BASE = "https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard/resolve/main"
ARENA_HTML_URL = "https://lmarena.ai/"

REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
USER_AGENT = "TopClanker-LLMScraper/1.0 (+https://github.com/burninmedia/topclanker)"

console = Console()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sleep_backoff(attempt: int) -> None:
    delay = 2 ** (attempt + 1)
    console.log(f"[lmsys_arena] retrying in {delay}s")
    time.sleep(delay)


def _http_get_json(client: httpx.Client, url: str) -> Any | None:
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 500, 502, 503, 504):
                _sleep_backoff(attempt)
                continue
            console.log(f"[lmsys_arena] unexpected status {resp.status_code} from {url}")
            return None
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            console.log(f"[lmsys_arena] transport error: {exc!r}")
            _sleep_backoff(attempt)
    return None


def _http_get_text(client: httpx.Client, url: str) -> str | None:
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code in (429, 500, 502, 503, 504):
                _sleep_backoff(attempt)
                continue
            console.log(f"[lmsys_arena] unexpected status {resp.status_code} from {url}")
            return None
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            console.log(f"[lmsys_arena] transport error: {exc!r}")
            _sleep_backoff(attempt)
    return None


def _coerce_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(float(str(val).replace(",", "").strip()))
    except (TypeError, ValueError):
        return None


def _coerce_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _pick_column(header: list[str], candidates: list[str]) -> int | None:
    lowered = [h.lower() for h in header]
    for cand in candidates:
        cand_l = cand.lower()
        for idx, col in enumerate(lowered):
            if cand_l == col or cand_l in col:
                return idx
    return None


def _fetch_via_space_csv(client: httpx.Client) -> list[dict[str, Any]]:
    """
    List files in the HF Space, pick the newest leaderboard_table_*.csv, parse it.
    """
    tree = _http_get_json(client, SPACE_TREE_API)
    if not isinstance(tree, list):
        return []

    csv_files = [
        entry["path"]
        for entry in tree
        if isinstance(entry, dict)
        and isinstance(entry.get("path"), str)
        and re.match(r"leaderboard_table_\d{8}\.csv$", entry["path"])
    ]
    if not csv_files:
        return []

    csv_files.sort(reverse=True)  # lexicographic sort == newest first for YYYYMMDD
    newest = csv_files[0]
    csv_url = f"{SPACE_FILE_BASE}/{newest}"
    console.log(f"[lmsys_arena] fetching CSV: {csv_url}")

    text = _http_get_text(client, csv_url)
    if not text:
        return []

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if len(rows) < 2:
        return []

    header = rows[0]
    model_idx = _pick_column(header, ["Model", "model", "key", "name"])
    elo_idx = _pick_column(header, ["Arena Elo", "Arena Score", "rating", "elo"])
    votes_idx = _pick_column(header, ["Votes", "num_battles", "battles", "count"])

    if model_idx is None or elo_idx is None:
        console.log(f"[lmsys_arena] CSV header missing required columns: {header}")
        return []

    records: list[dict[str, Any]] = []
    for row in rows[1:]:
        if len(row) <= max(model_idx, elo_idx):
            continue
        model_name = row[model_idx].strip()
        if not model_name:
            continue
        elo = _coerce_float(row[elo_idx])
        if elo is None:
            continue
        votes = _coerce_int(row[votes_idx]) if votes_idx is not None and votes_idx < len(row) else None
        record: dict[str, Any] = {
            "model_raw_name": model_name,
            "benchmark": BENCHMARK_KEY,
            "score": round(elo, 1),
        }
        if votes is not None:
            record["votes"] = votes
        records.append(record)

    return records


def _fetch_via_html(client: httpx.Client) -> list[dict[str, Any]]:
    html = _http_get_text(client, ARENA_HTML_URL)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, Any]] = []

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not headers:
            continue
        model_idx = _pick_column(headers, ["Model", "model"])
        elo_idx = _pick_column(headers, ["Arena Elo", "Arena Score", "Elo", "Rating"])
        votes_idx = _pick_column(headers, ["Votes", "Battles", "# Votes"])
        if model_idx is None or elo_idx is None:
            continue

        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) <= max(model_idx, elo_idx):
                continue
            model_name = tds[model_idx].get_text(strip=True)
            if not model_name:
                continue
            elo = _coerce_float(tds[elo_idx].get_text(strip=True))
            if elo is None:
                continue
            votes = None
            if votes_idx is not None and votes_idx < len(tds):
                votes = _coerce_int(tds[votes_idx].get_text(strip=True))
            record: dict[str, Any] = {
                "model_raw_name": model_name,
                "benchmark": BENCHMARK_KEY,
                "score": round(elo, 1),
            }
            if votes is not None:
                record["votes"] = votes
            records.append(record)

        if records:
            break  # first usable table wins

    return records


def run_scraper() -> bool:
    """Entry point called by the orchestrator. Never raises."""
    console.log(f"[lmsys_arena] starting scrape at {_now_iso()}")
    try:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        headers = {"User-Agent": USER_AGENT, "Accept": "application/json,text/html,text/csv"}
        with httpx.Client(timeout=REQUEST_TIMEOUT, headers=headers, follow_redirects=True) as client:
            records = _fetch_via_space_csv(client)
            if records:
                console.log(f"[lmsys_arena] CSV returned {len(records)} records")
            else:
                console.log("[lmsys_arena] CSV empty, trying HTML fallback")
                records = _fetch_via_html(client)
                console.log(f"[lmsys_arena] HTML fallback returned {len(records)} records")

        payload = {
            "source": SOURCE_NAME,
            "scraped_at": _now_iso(),
            "records": records,
        }
        OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.log(f"[lmsys_arena] wrote {len(records)} records -> {OUTPUT_PATH}")
        return True

    except Exception as exc:  # noqa: BLE001 — orchestrator contract: never raise
        console.log(f"[lmsys_arena] FAILED with {exc!r}")
        try:
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT_PATH.write_text(
                json.dumps(
                    {"source": SOURCE_NAME, "scraped_at": _now_iso(), "records": []},
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:  # noqa: BLE001
            pass
        return False


if __name__ == "__main__":
    ok = run_scraper()
    raise SystemExit(0 if ok else 1)
