"""
Scraper for the Hugging Face Open LLM Leaderboard.

Primary path: fetch rows via the HF datasets-server API.
Fallback:     scrape the HTML table from the public Space page.

Output file: data/raw/hf_leaderboard.json
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from rich.console import Console

SOURCE_NAME = "hf_leaderboard"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "hf_leaderboard.json"

DATASETS_SERVER_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=open-llm-leaderboard%2Fresults"
    "&config=default"
    "&split=train"
)
SPACE_HTML_URL = "https://huggingface.co/spaces/open-llm-leaderboard/open-llm-leaderboard"

# Canonical benchmark keys we emit. Column names from the HF dataset are matched
# fuzzily against these keys (case-insensitive substring match).
BENCHMARK_COLUMN_MAP = {
    "mmlu": "mmlu",
    "arc": "arc",
    "hellaswag": "hellaswag",
    "truthfulqa": "truthfulqa",
    "winogrande": "winogrande",
    "gsm8k": "gsm8k",
}

REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
USER_AGENT = "TopClanker-LLMScraper/1.0 (+https://github.com/burninmedia/topclanker)"

console = Console()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sleep_backoff(attempt: int) -> None:
    """Exponential backoff with simple jitter-free doubling: 2s, 4s, 8s."""
    delay = 2 ** (attempt + 1)
    console.log(f"[hf_leaderboard] rate-limited / failed, sleeping {delay}s before retry")
    time.sleep(delay)


def _http_get_json(client: httpx.Client, url: str) -> dict[str, Any] | None:
    """GET a URL expecting JSON, with exponential backoff on 429/5xx."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 500, 502, 503, 504):
                _sleep_backoff(attempt)
                continue
            console.log(f"[hf_leaderboard] unexpected status {resp.status_code} from {url}")
            return None
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            console.log(f"[hf_leaderboard] transport error: {exc!r}")
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
            console.log(f"[hf_leaderboard] unexpected status {resp.status_code} from {url}")
            return None
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            console.log(f"[hf_leaderboard] transport error: {exc!r}")
            _sleep_backoff(attempt)
    return None


def _map_column_to_benchmark(column_name: str) -> str | None:
    """Resolve a dataset column header to one of our canonical benchmark keys."""
    lowered = column_name.lower().replace("-", "").replace("_", "").replace(" ", "")
    for canonical, token in BENCHMARK_COLUMN_MAP.items():
        if token in lowered:
            return canonical
    return None


def _extract_model_name(row: dict[str, Any]) -> str | None:
    for key in ("model", "Model", "model_name", "fullname", "full_name", "model_id"):
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _coerce_score(value: Any) -> float | None:
    if value is None:
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    # HF leaderboard sometimes reports accuracies in 0–1 range, sometimes 0–100.
    if 0.0 <= score <= 1.0:
        score *= 100.0
    return round(score, 2)


def _fetch_via_datasets_api(client: httpx.Client) -> list[dict[str, Any]]:
    """
    Page through the HF datasets-server API. Returns a list of normalized records.
    Each record: {model_raw_name, benchmark, score}.
    """
    records: list[dict[str, Any]] = []
    offset = 0
    page_size = 100

    while True:
        url = f"{DATASETS_SERVER_URL}&offset={offset}&length={page_size}"
        payload = _http_get_json(client, url)
        if not payload:
            break

        rows = payload.get("rows", [])
        if not rows:
            break

        for wrapper in rows:
            row = wrapper.get("row", {}) if isinstance(wrapper, dict) else {}
            model = _extract_model_name(row)
            if not model:
                continue
            for column, value in row.items():
                benchmark = _map_column_to_benchmark(column)
                if benchmark is None:
                    continue
                score = _coerce_score(value)
                if score is None:
                    continue
                records.append(
                    {
                        "model_raw_name": model,
                        "benchmark": benchmark,
                        "score": score,
                    }
                )

        if len(rows) < page_size:
            break
        offset += page_size
        # Politeness pause between pages.
        time.sleep(0.5)

    return records


def _fetch_via_html(client: httpx.Client) -> list[dict[str, Any]]:
    """Fallback: parse the Space HTML. Best-effort; may yield nothing if the table is JS-rendered."""
    html = _http_get_text(client, SPACE_HTML_URL)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, Any]] = []

    for table in soup.find_all("table"):
        header_cells = [th.get_text(strip=True) for th in table.find_all("th")]
        if not header_cells:
            continue
        # Map each header column index to a canonical benchmark key (or None for model name).
        column_to_benchmark: dict[int, str | None] = {}
        model_col_idx: int | None = None
        for idx, header in enumerate(header_cells):
            if header.lower() in ("model", "name"):
                model_col_idx = idx
                column_to_benchmark[idx] = None
            else:
                column_to_benchmark[idx] = _map_column_to_benchmark(header)

        if model_col_idx is None or not any(column_to_benchmark.values()):
            continue

        for row in table.find_all("tr"):
            cells = row.find_all(["td"])
            if not cells:
                continue
            if model_col_idx >= len(cells):
                continue
            model = cells[model_col_idx].get_text(strip=True)
            if not model:
                continue
            for idx, cell in enumerate(cells):
                benchmark = column_to_benchmark.get(idx)
                if not benchmark:
                    continue
                score = _coerce_score(cell.get_text(strip=True))
                if score is None:
                    continue
                records.append(
                    {
                        "model_raw_name": model,
                        "benchmark": benchmark,
                        "score": score,
                    }
                )

    return records


def run_scraper() -> bool:
    """Entry point called by the orchestrator. Never raises."""
    console.log(f"[hf_leaderboard] starting scrape at {_now_iso()}")
    try:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        with httpx.Client(timeout=REQUEST_TIMEOUT, headers=headers, follow_redirects=True) as client:
            records = _fetch_via_datasets_api(client)
            if records:
                console.log(f"[hf_leaderboard] datasets API returned {len(records)} records")
            else:
                console.log("[hf_leaderboard] datasets API empty, trying HTML fallback")
                records = _fetch_via_html(client)
                console.log(f"[hf_leaderboard] HTML fallback returned {len(records)} records")

        payload = {
            "source": SOURCE_NAME,
            "scraped_at": _now_iso(),
            "records": records,
        }
        OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.log(f"[hf_leaderboard] wrote {len(records)} records -> {OUTPUT_PATH}")
        return True

    except Exception as exc:  # noqa: BLE001 — orchestrator contract: never raise
        console.log(f"[hf_leaderboard] FAILED with {exc!r}")
        # Still write an empty stub so downstream stages see a consistent file.
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
