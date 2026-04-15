"""
Scraper for the Hugging Face Open LLM Leaderboard v2.

v1 (MMLU / ARC / HellaSwag / TruthfulQA / Winogrande / GSM8K) has been
retired upstream; its Space HTML is gated (401) and the `results` dataset
404s. v2 publishes its data through the `open-llm-leaderboard/contents`
dataset, which we read in priority order:

  1. HF datasets-server JSON rows endpoint (no auth, paginated).
  2. The parquet files advertised by the HF hub dataset tree API, fetched
     as bytes and read with pyarrow. Tried in order from smallest file
     upward to keep CI fast.
  3. Old HTML fallback on the public Space URL (likely still 401, kept
     only as a last-resort safety net).

Output: data/raw/hf_leaderboard.json
"""

from __future__ import annotations

import io
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

# v2 canonical dataset. Public, no auth required for reads.
DATASET_ID = "open-llm-leaderboard/contents"

DATASETS_SERVER_URL = (
    "https://datasets-server.huggingface.co/rows"
    f"?dataset={DATASET_ID.replace('/', '%2F')}"
    "&config=default"
    "&split=train"
)
DATASET_TREE_API = f"https://huggingface.co/api/datasets/{DATASET_ID}/tree/main"
DATASET_FILE_BASE = f"https://huggingface.co/datasets/{DATASET_ID}/resolve/main"
SPACE_HTML_URL = "https://huggingface.co/spaces/open-llm-leaderboard/open-llm-leaderboard"

# v2 benchmark set. Keys must match `data/benchmarks.json`.
#
# Upstream column headers vary (`IFEval`, `leaderboard_ifeval`,
# `IFEval (0-shot)`, etc.). We match by normalised substring token.
BENCHMARK_COLUMN_TOKENS: dict[str, tuple[str, ...]] = {
    "ifeval":    ("ifeval", "instructionfollowing"),
    "bbh":       ("bbh", "bigbenchhard"),
    "math_lvl5": ("mathlvl5", "mathlevel5", "math5shot", "mathhard"),
    "gpqa":      ("gpqa",),
    "musr":      ("musr",),
    "mmlu_pro":  ("mmlupro",),
}

# Common column names that hold the model identifier in the v2 dataset.
MODEL_NAME_KEYS = (
    "fullname",
    "eval_name",
    "full_name",
    "model",
    "model_name",
    "Model",
    "model_id",
)

REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
USER_AGENT = "TopClanker-LLMScraper/1.0 (+https://github.com/burninmedia/topclanker)"
PAGE_SIZE = 100
# Parquet files over this many bytes get skipped to keep CI bounded.
PARQUET_MAX_BYTES = 25 * 1024 * 1024

console = Console()


# ---------- small HTTP / parsing helpers ----------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sleep_backoff(attempt: int) -> None:
    delay = 2 ** (attempt + 1)
    console.log(f"[hf_leaderboard] retrying in {delay}s")
    time.sleep(delay)


def _retryable_get(client: httpx.Client, url: str) -> httpx.Response | None:
    """GET `url`, retrying with exponential backoff on 429/5xx. Returns the
    final response (even if non-200), or None if transport-level failures
    exhausted retries."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.get(url)
            if resp.status_code in (429, 500, 502, 503, 504):
                _sleep_backoff(attempt)
                continue
            return resp
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            console.log(f"[hf_leaderboard] transport error: {exc!r}")
            _sleep_backoff(attempt)
    return None


def _http_get_json(client: httpx.Client, url: str) -> Any | None:
    resp = _retryable_get(client, url)
    if resp is None or resp.status_code != 200:
        if resp is not None:
            console.log(f"[hf_leaderboard] status {resp.status_code} from {url}")
        return None
    try:
        return resp.json()
    except ValueError:
        return None


def _http_get_text(client: httpx.Client, url: str) -> str | None:
    resp = _retryable_get(client, url)
    if resp is None or resp.status_code != 200:
        if resp is not None:
            console.log(f"[hf_leaderboard] status {resp.status_code} from {url}")
        return None
    return resp.text


def _http_get_bytes(client: httpx.Client, url: str) -> bytes | None:
    resp = _retryable_get(client, url)
    if resp is None or resp.status_code != 200:
        if resp is not None:
            console.log(f"[hf_leaderboard] status {resp.status_code} from {url}")
        return None
    return resp.content


def _normalise_col(name: str) -> str:
    return (
        name.lower()
        .replace("-", "")
        .replace("_", "")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
    )


def _map_column_to_benchmark(column_name: str) -> str | None:
    """Resolve a dataset column header to one of our canonical benchmark keys
    via normalised-substring match. Case- and separator-insensitive."""
    if not isinstance(column_name, str):
        return None
    normalised = _normalise_col(column_name)
    if not normalised:
        return None
    for canonical, tokens in BENCHMARK_COLUMN_TOKENS.items():
        for token in tokens:
            if token in normalised:
                return canonical
    return None


def _extract_model_name(row: dict[str, Any]) -> str | None:
    for key in MODEL_NAME_KEYS:
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
    # v2 reports accuracies both as 0-1 ratios and 0-100 percents.
    if 0.0 <= score <= 1.0:
        score *= 100.0
    return round(score, 2)


def _rows_to_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
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
                {"model_raw_name": model, "benchmark": benchmark, "score": score}
            )
    return records


# ---------- source 1: datasets-server JSON rows ----------


def _fetch_via_datasets_server(client: httpx.Client) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    offset = 0
    while True:
        url = f"{DATASETS_SERVER_URL}&offset={offset}&length={PAGE_SIZE}"
        payload = _http_get_json(client, url)
        if not payload:
            break
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        if not rows:
            break
        inner = []
        for wrapper in rows:
            if isinstance(wrapper, dict) and isinstance(wrapper.get("row"), dict):
                inner.append(wrapper["row"])
        records.extend(_rows_to_records(inner))
        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(0.3)
    return records


# ---------- source 2: parquet via HF hub file API ----------


def _list_parquet_files(client: httpx.Client) -> list[dict[str, Any]]:
    """Walk the dataset tree and return parquet file entries with size info."""
    tree = _http_get_json(client, DATASET_TREE_API)
    if not isinstance(tree, list):
        return []
    parquet: list[dict[str, Any]] = []
    for entry in tree:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if isinstance(path, str) and path.endswith(".parquet"):
            parquet.append(
                {
                    "path": path,
                    "size": entry.get("size") or 0,
                }
            )
        # The contents dataset sometimes nests parquet under data/; follow one level.
        if (
            isinstance(path, str)
            and entry.get("type") == "directory"
            and path in ("data", "train")
        ):
            sub = _http_get_json(client, f"{DATASET_TREE_API}/{path}")
            if isinstance(sub, list):
                for child in sub:
                    if (
                        isinstance(child, dict)
                        and isinstance(child.get("path"), str)
                        and child["path"].endswith(".parquet")
                    ):
                        parquet.append({"path": child["path"], "size": child.get("size") or 0})
    # Prefer the smallest file — faster in CI, and the leaderboard table is
    # a single shard in practice.
    parquet.sort(key=lambda e: e["size"] if e["size"] else 1 << 60)
    return parquet


def _fetch_via_parquet(client: httpx.Client) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError:
        console.log("[hf_leaderboard] pyarrow not installed; skipping parquet path")
        return []

    files = _list_parquet_files(client)
    if not files:
        return []

    for entry in files:
        if entry["size"] and entry["size"] > PARQUET_MAX_BYTES:
            console.log(
                f"[hf_leaderboard] skipping oversized parquet {entry['path']} "
                f"({entry['size']} bytes > {PARQUET_MAX_BYTES})"
            )
            continue
        url = f"{DATASET_FILE_BASE}/{entry['path']}"
        console.log(f"[hf_leaderboard] fetching parquet {url}")
        blob = _http_get_bytes(client, url)
        if not blob:
            continue
        try:
            table = pq.read_table(io.BytesIO(blob))
        except Exception as exc:  # noqa: BLE001
            console.log(f"[hf_leaderboard] parquet parse error on {entry['path']}: {exc!r}")
            continue
        rows = table.to_pylist()
        records = _rows_to_records(rows)
        if records:
            return records
    return []


# ---------- source 3: HTML fallback (likely still gated) ----------


def _fetch_via_html(client: httpx.Client) -> list[dict[str, Any]]:
    html = _http_get_text(client, SPACE_HTML_URL)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, Any]] = []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not headers:
            continue
        col_to_bench: dict[int, str | None] = {}
        model_idx: int | None = None
        for idx, header in enumerate(headers):
            if header.lower() in ("model", "name", "eval name"):
                model_idx = idx
                col_to_bench[idx] = None
            else:
                col_to_bench[idx] = _map_column_to_benchmark(header)
        if model_idx is None or not any(col_to_bench.values()):
            continue
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) <= model_idx:
                continue
            model = cells[model_idx].get_text(strip=True)
            if not model:
                continue
            for idx, cell in enumerate(cells):
                bench = col_to_bench.get(idx)
                if not bench:
                    continue
                score = _coerce_score(cell.get_text(strip=True))
                if score is None:
                    continue
                records.append(
                    {"model_raw_name": model, "benchmark": bench, "score": score}
                )
    return records


# ---------- orchestration ----------


def run_scraper() -> bool:
    """Entry point called by the orchestrator. Never raises."""
    console.log(f"[hf_leaderboard] starting scrape at {_now_iso()}")
    try:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        with httpx.Client(timeout=REQUEST_TIMEOUT, headers=headers, follow_redirects=True) as client:
            for label, fetch_fn in (
                ("datasets-server", _fetch_via_datasets_server),
                ("parquet", _fetch_via_parquet),
                ("html", _fetch_via_html),
            ):
                try:
                    records = fetch_fn(client)
                except Exception as exc:  # noqa: BLE001
                    console.log(f"[hf_leaderboard] {label} raised {exc!r}")
                    records = []
                if records:
                    console.log(
                        f"[hf_leaderboard] {label} returned {len(records)} records"
                    )
                    break
                console.log(f"[hf_leaderboard] {label} returned 0 records")
            else:
                records = []

        payload = {
            "source": SOURCE_NAME,
            "scraped_at": _now_iso(),
            "records": records,
        }
        OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.log(f"[hf_leaderboard] wrote {len(records)} records -> {OUTPUT_PATH}")
        return True

    except Exception as exc:  # noqa: BLE001 — orchestrator contract
        console.log(f"[hf_leaderboard] FAILED with {exc!r}")
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
