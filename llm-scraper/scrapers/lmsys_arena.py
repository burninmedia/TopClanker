"""
Scraper for the LMSYS Chatbot Arena Elo leaderboard.

The CSVs historically published under `lmsys/chatbot-arena-leaderboard` no
longer carry Arena Elo columns (they are stale pre-Arena leaderboard
tables). Actual Arena Elo data is published in two places:

  1. `elo_results_YYYYMMDD.pkl` inside the HF Space — a pickled pandas
     object containing DataFrames keyed by model with `rating` and
     `num_battles` columns.
  2. `lmarena.ai` — the successor site. We probe for a JSON API and fall
     back to HTML scraping of the leaderboard page.

Per user decision: if no Arena Elo source is reachable, this scraper
reports 0 records rather than degrading to MT-bench. 0 records is the
correct signal for the smoke test to flag an upstream break.

SECURITY NOTE: `pickle.load` executes arbitrary code from the opener. We
only ever unpickle bytes fetched over HTTPS from `huggingface.co`,
bounded by PKL_MAX_BYTES and a fixed timeout. Do not reuse this code
path for untrusted sources.

Output: data/raw/lmsys_arena.json
"""

from __future__ import annotations

import io
import json
import pickle
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

LMARENA_API_CANDIDATES = (
    "https://lmarena.ai/api/leaderboard",
    "https://lmarena.ai/api/public/leaderboard",
    "https://lmarena.ai/api/leaderboard/overview",
)
LMARENA_HTML_URL = "https://lmarena.ai/leaderboard"

REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
USER_AGENT = "TopClanker-LLMScraper/1.0 (+https://github.com/burninmedia/topclanker)"
PKL_MAX_BYTES = 50 * 1024 * 1024  # cap on what we'll unpickle

# Column-name candidates inside the elo_results DataFrames.
RATING_COLS = ("rating", "arena_elo", "arena_score", "elo", "score")
VOTES_COLS = ("num_battles", "votes", "battles", "count", "num_votes")
MODEL_COLS = ("model", "model_name", "key", "name")

console = Console()


# ---------- HTTP helpers ----------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sleep_backoff(attempt: int) -> None:
    delay = 2 ** (attempt + 1)
    console.log(f"[lmsys_arena] retrying in {delay}s")
    time.sleep(delay)


def _retryable_get(client: httpx.Client, url: str) -> httpx.Response | None:
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.get(url)
            if resp.status_code in (429, 500, 502, 503, 504):
                _sleep_backoff(attempt)
                continue
            return resp
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            console.log(f"[lmsys_arena] transport error: {exc!r}")
            _sleep_backoff(attempt)
    return None


def _http_get_json(client: httpx.Client, url: str) -> Any | None:
    resp = _retryable_get(client, url)
    if resp is None or resp.status_code != 200:
        if resp is not None:
            console.log(f"[lmsys_arena] status {resp.status_code} from {url}")
        return None
    try:
        return resp.json()
    except ValueError:
        return None


def _http_get_text(client: httpx.Client, url: str) -> str | None:
    resp = _retryable_get(client, url)
    if resp is None or resp.status_code != 200:
        if resp is not None:
            console.log(f"[lmsys_arena] status {resp.status_code} from {url}")
        return None
    return resp.text


def _http_get_bytes(client: httpx.Client, url: str, max_bytes: int | None = None) -> bytes | None:
    resp = _retryable_get(client, url)
    if resp is None or resp.status_code != 200:
        if resp is not None:
            console.log(f"[lmsys_arena] status {resp.status_code} from {url}")
        return None
    content = resp.content
    if max_bytes is not None and len(content) > max_bytes:
        console.log(
            f"[lmsys_arena] refusing {url}: {len(content)} bytes > cap {max_bytes}"
        )
        return None
    return content


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


def _pick_column(header: list[str], candidates: tuple[str, ...] | list[str]) -> int | None:
    lowered = [h.lower() if isinstance(h, str) else "" for h in header]
    for cand in candidates:
        cand_l = cand.lower()
        for idx, col in enumerate(lowered):
            if cand_l == col or cand_l in col:
                return idx
    return None


# ---------- source 1: elo_results_*.pkl inside the HF Space ----------


def _collect_records_from_dataframe(obj: Any) -> list[dict[str, Any]]:
    """Given a pandas DataFrame, extract (model, rating, votes) rows if its
    schema looks Elo-shaped. Returns [] if not applicable."""
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return []

    if not isinstance(obj, pd.DataFrame) or obj.empty:
        return []

    df = obj
    columns = list(df.columns)
    col_strs = [str(c) for c in columns]

    rating_idx = None
    for i, name in enumerate(col_strs):
        if name.lower() in RATING_COLS:
            rating_idx = i
            break
    if rating_idx is None:
        return []

    model_idx = None
    for i, name in enumerate(col_strs):
        if name.lower() in MODEL_COLS:
            model_idx = i
            break

    votes_idx = None
    for i, name in enumerate(col_strs):
        if name.lower() in VOTES_COLS:
            votes_idx = i
            break

    records: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        # Model name: prefer a named column, fall back to the row index.
        if model_idx is not None:
            raw_model = row.iloc[model_idx]
        else:
            raw_model = idx
        if raw_model is None or (hasattr(pd, "isna") and pd.isna(raw_model)):
            continue
        model = str(raw_model).strip()
        if not model:
            continue

        raw_rating = row.iloc[rating_idx]
        if raw_rating is None or (hasattr(pd, "isna") and pd.isna(raw_rating)):
            continue
        try:
            rating = float(raw_rating)
        except (TypeError, ValueError):
            continue

        record: dict[str, Any] = {
            "model_raw_name": model,
            "benchmark": BENCHMARK_KEY,
            "score": round(rating, 1),
        }
        if votes_idx is not None:
            raw_votes = row.iloc[votes_idx]
            if raw_votes is not None and not (hasattr(pd, "isna") and pd.isna(raw_votes)):
                try:
                    record["votes"] = int(raw_votes)
                except (TypeError, ValueError):
                    pass
        records.append(record)
    return records


def _walk_pickle_for_elo(payload: Any, seen_ids: set[int] | None = None) -> list[dict[str, Any]]:
    """Traverse an unpickled blob looking for the first DataFrame with an
    Elo-shaped schema. `seen_ids` guards against self-referential structures."""
    if seen_ids is None:
        seen_ids = set()
    oid = id(payload)
    if oid in seen_ids:
        return []
    seen_ids.add(oid)

    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return []

    if isinstance(payload, pd.DataFrame):
        recs = _collect_records_from_dataframe(payload)
        if recs:
            return recs
        return []

    if isinstance(payload, dict):
        for v in payload.values():
            recs = _walk_pickle_for_elo(v, seen_ids)
            if recs:
                return recs
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            recs = _walk_pickle_for_elo(v, seen_ids)
            if recs:
                return recs
    return []


def _fetch_via_elo_pickle(client: httpx.Client) -> list[dict[str, Any]]:
    tree = _http_get_json(client, SPACE_TREE_API)
    if not isinstance(tree, list):
        return []
    pkls = [
        entry["path"]
        for entry in tree
        if isinstance(entry, dict)
        and isinstance(entry.get("path"), str)
        and re.match(r"elo_results_\d{8}\.pkl$", entry["path"])
    ]
    if not pkls:
        console.log("[lmsys_arena] no elo_results_*.pkl files in Space tree")
        return []
    pkls.sort(reverse=True)  # lexicographic sort == newest YYYYMMDD first
    for name in pkls:
        url = f"{SPACE_FILE_BASE}/{name}"
        console.log(f"[lmsys_arena] fetching pickle: {url}")
        blob = _http_get_bytes(client, url, max_bytes=PKL_MAX_BYTES)
        if not blob:
            continue
        try:
            # SECURITY: only unpickle bytes fetched over HTTPS from huggingface.co.
            payload = pickle.loads(blob)  # noqa: S301
        except Exception as exc:  # noqa: BLE001
            console.log(f"[lmsys_arena] pickle load error on {name}: {exc!r}")
            continue
        records = _walk_pickle_for_elo(payload)
        if records:
            return records
        console.log(f"[lmsys_arena] pickle {name} had no Elo-shaped DataFrame")
    return []


# ---------- source 2: lmarena.ai JSON API ----------


def _records_from_json_payload(payload: Any) -> list[dict[str, Any]]:
    """Best-effort extraction from a JSON response. lmarena.ai has changed
    shape historically; accept a list of dicts OR a dict containing a list
    under common key names."""
    candidates: list[Any] = []
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        for key in ("models", "leaderboard", "results", "data", "entries", "items"):
            val = payload.get(key)
            if isinstance(val, list):
                candidates = val
                break
    if not candidates:
        return []
    records: list[dict[str, Any]] = []
    for row in candidates:
        if not isinstance(row, dict):
            continue
        model = None
        for key in MODEL_COLS:
            v = row.get(key)
            if isinstance(v, str) and v.strip():
                model = v.strip()
                break
        if not model:
            continue
        rating = None
        for key in RATING_COLS:
            v = row.get(key)
            coerced = _coerce_float(v)
            if coerced is not None:
                rating = coerced
                break
        if rating is None:
            continue
        votes = None
        for key in VOTES_COLS:
            v = row.get(key)
            coerced = _coerce_int(v)
            if coerced is not None:
                votes = coerced
                break
        record: dict[str, Any] = {
            "model_raw_name": model,
            "benchmark": BENCHMARK_KEY,
            "score": round(rating, 1),
        }
        if votes is not None:
            record["votes"] = votes
        records.append(record)
    return records


def _fetch_via_lmarena_api(client: httpx.Client) -> list[dict[str, Any]]:
    for url in LMARENA_API_CANDIDATES:
        console.log(f"[lmsys_arena] probing JSON: {url}")
        payload = _http_get_json(client, url)
        if not payload:
            continue
        records = _records_from_json_payload(payload)
        if records:
            return records
    return []


# ---------- source 3: lmarena.ai HTML scrape ----------


def _fetch_via_lmarena_html(client: httpx.Client) -> list[dict[str, Any]]:
    html = _http_get_text(client, LMARENA_HTML_URL)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not headers:
            continue
        model_idx = _pick_column(headers, list(MODEL_COLS) + ["Model"])
        rating_idx = _pick_column(
            headers,
            list(RATING_COLS) + ["Arena Elo", "Arena Score", "Rating"],
        )
        votes_idx = _pick_column(
            headers, list(VOTES_COLS) + ["Votes", "Battles", "# Votes"]
        )
        if model_idx is None or rating_idx is None:
            continue
        records: list[dict[str, Any]] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) <= max(model_idx, rating_idx):
                continue
            model = cells[model_idx].get_text(strip=True)
            if not model:
                continue
            rating = _coerce_float(cells[rating_idx].get_text(strip=True))
            if rating is None:
                continue
            record: dict[str, Any] = {
                "model_raw_name": model,
                "benchmark": BENCHMARK_KEY,
                "score": round(rating, 1),
            }
            if votes_idx is not None and votes_idx < len(cells):
                v = _coerce_int(cells[votes_idx].get_text(strip=True))
                if v is not None:
                    record["votes"] = v
            records.append(record)
        if records:
            return records
    return []


# ---------- orchestration ----------


def run_scraper() -> bool:
    """Entry point. Never raises."""
    console.log(f"[lmsys_arena] starting scrape at {_now_iso()}")
    try:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        headers = {"User-Agent": USER_AGENT, "Accept": "application/json,text/html"}
        records: list[dict[str, Any]] = []
        with httpx.Client(timeout=REQUEST_TIMEOUT, headers=headers, follow_redirects=True) as client:
            for label, fetch_fn in (
                ("elo_pickle", _fetch_via_elo_pickle),
                ("lmarena_api", _fetch_via_lmarena_api),
                ("lmarena_html", _fetch_via_lmarena_html),
            ):
                try:
                    got = fetch_fn(client)
                except Exception as exc:  # noqa: BLE001
                    console.log(f"[lmsys_arena] {label} raised {exc!r}")
                    got = []
                if got:
                    console.log(f"[lmsys_arena] {label} returned {len(got)} records")
                    records = got
                    break
                console.log(f"[lmsys_arena] {label} returned 0 records")

        payload = {
            "source": SOURCE_NAME,
            "scraped_at": _now_iso(),
            "records": records,
        }
        OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.log(f"[lmsys_arena] wrote {len(records)} records -> {OUTPUT_PATH}")
        return True

    except Exception as exc:  # noqa: BLE001 — orchestrator contract
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
