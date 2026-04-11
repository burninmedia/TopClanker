"""
Normalize raw scraper output into the canonical master.json dataset.

Responsibilities
----------------
1. Load benchmarks.json and models.json.
2. Build an alias lookup: alias string -> (key, canonical_id, display_name, provider).
3. Load every data/raw/*.json file, iterate each record.
4. Resolve each record's model to a canonical_id or flag it for human review.
5. Merge resolved records into master.json following the authoritative-source
   overwrite rule:

     * New model                      -> add, set first_seen & last_updated.
     * Existing model + new benchmark -> add the score.
     * Existing model + existing score:
         incoming.source == benchmarks[bench].authoritative_source
             -> overwrite
         otherwise
             -> keep existing, skip.

6. Attach benchmark_type (from benchmarks.json) to every score entry so the
   consuming site can group/compare apples-to-apples without a join.

7. Write master.json and append new unknown names to needs_review.json
   (deduplicated by raw_name).

Return value: number of NEW raw_names added to needs_review.json this run.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

BENCHMARKS_PATH = DATA_DIR / "benchmarks.json"
MODELS_PATH = DATA_DIR / "models.json"
MASTER_PATH = DATA_DIR / "master.json"
NEEDS_REVIEW_PATH = DATA_DIR / "needs_review.json"

console = Console()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.log(f"[normalize] WARNING: {path} is invalid JSON ({exc}); using default")
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _build_alias_lookup(models: dict[str, Any]) -> dict[str, dict[str, str]]:
    """
    Return a case-insensitive lookup from any alias string to the model's metadata.
    Key: normalized alias (lowercased, stripped).
    Value: {canonical_id, display_name, provider, registry_key}.
    """
    lookup: dict[str, dict[str, str]] = {}
    for registry_key, entry in models.items():
        canonical_id = entry.get("canonical_id")
        display_name = entry.get("display_name", canonical_id)
        provider = entry.get("provider", "Unknown")
        aliases = set(entry.get("aliases", []))
        # The registry key itself and the canonical id should always resolve.
        aliases.add(registry_key)
        if canonical_id:
            aliases.add(canonical_id)
        for alias in aliases:
            if not isinstance(alias, str):
                continue
            key = alias.strip().lower()
            if not key:
                continue
            lookup[key] = {
                "canonical_id": canonical_id,
                "display_name": display_name,
                "provider": provider,
                "registry_key": registry_key,
            }
    return lookup


def _load_raw_records() -> list[tuple[str, dict[str, Any]]]:
    """
    Return a list of (source_name, record) tuples collected from every
    data/raw/*.json file. Robust to files that are missing or malformed.
    """
    collected: list[tuple[str, dict[str, Any]]] = []
    if not RAW_DIR.exists():
        return collected

    for path in sorted(RAW_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.log(f"[normalize] skipping {path.name}: {exc}")
            continue
        if not isinstance(payload, dict):
            continue
        source = payload.get("source") or path.stem
        records = payload.get("records") or []
        if not isinstance(records, list):
            continue
        for rec in records:
            if isinstance(rec, dict):
                collected.append((source, rec))

    return collected


def _append_needs_review(new_unknowns: list[dict[str, str]]) -> int:
    """Append new entries to needs_review.json, deduplicating by raw_name. Returns new-count."""
    current = _load_json(NEEDS_REVIEW_PATH, {"last_updated": None, "pending": []})
    pending = current.get("pending", []) or []
    existing_names = {entry.get("raw_name") for entry in pending if isinstance(entry, dict)}

    added = 0
    for entry in new_unknowns:
        if entry["raw_name"] in existing_names:
            continue
        pending.append(entry)
        existing_names.add(entry["raw_name"])
        added += 1

    if added:
        current["pending"] = pending
        current["last_updated"] = _now_iso()
        _write_json(NEEDS_REVIEW_PATH, current)
    return added


def normalize() -> int:
    """
    Run the normalization stage. Returns the number of NEW names flagged for
    human review in this run (0 = all names resolved cleanly).
    """
    now = _now_iso()

    benchmarks = _load_json(BENCHMARKS_PATH, {})
    models = _load_json(MODELS_PATH, {})
    master = _load_json(
        MASTER_PATH,
        {"generated_at": None, "schema_version": "1", "models": {}},
    )
    master_models: dict[str, Any] = master.get("models") or {}

    alias_lookup = _build_alias_lookup(models)
    console.log(f"[normalize] alias lookup contains {len(alias_lookup)} entries")

    raw_records = _load_raw_records()
    console.log(f"[normalize] loaded {len(raw_records)} raw records")

    # Track unknowns to append to needs_review in a single pass (deduped within this run).
    unknowns_this_run: dict[str, dict[str, str]] = {}

    overwrites = 0
    additions = 0
    skipped_lower_source = 0
    resolved_records = 0

    for source, record in raw_records:
        raw_name = record.get("model_raw_name")
        benchmark = record.get("benchmark")
        score = record.get("score")

        if not isinstance(raw_name, str) or not raw_name.strip():
            continue
        if not isinstance(benchmark, str) or not benchmark:
            continue
        if not isinstance(score, (int, float)):
            continue

        lookup_key = raw_name.strip().lower()
        meta = alias_lookup.get(lookup_key)
        if meta is None:
            # Not a known alias — queue for human review and skip the record.
            if raw_name not in unknowns_this_run:
                unknowns_this_run[raw_name] = {
                    "raw_name": raw_name,
                    "source": source,
                    "first_seen": now,
                }
            continue

        resolved_records += 1
        canonical_id = meta["canonical_id"]
        bench_meta = benchmarks.get(benchmark, {}) if isinstance(benchmarks, dict) else {}
        benchmark_type = bench_meta.get("benchmark_type")
        authoritative_source = bench_meta.get("authoritative_source")

        # --- upsert model entry ---
        model_entry = master_models.get(canonical_id)
        if model_entry is None:
            model_entry = {
                "display_name": meta["display_name"],
                "provider": meta["provider"],
                "first_seen": now,
                "last_updated": now,
                "scores": {},
            }
            master_models[canonical_id] = model_entry

        scores: dict[str, Any] = model_entry.setdefault("scores", {})
        existing = scores.get(benchmark)

        new_score_obj = {
            "score": float(score),
            "source": source,
            "recorded_at": now,
        }
        if benchmark_type:
            new_score_obj["benchmark_type"] = benchmark_type
        # Carry optional metadata (e.g. votes for lmsys_elo) if present on the raw record.
        if "votes" in record and isinstance(record["votes"], int):
            new_score_obj["votes"] = record["votes"]

        if existing is None:
            scores[benchmark] = new_score_obj
            model_entry["last_updated"] = now
            additions += 1
            continue

        # Existing score present. Apply authoritative-source rule.
        if authoritative_source and source != authoritative_source:
            # Keep the existing score. BUT if existing is missing benchmark_type
            # and we now have one, backfill it without disturbing score/source.
            if benchmark_type and "benchmark_type" not in existing:
                existing["benchmark_type"] = benchmark_type
            skipped_lower_source += 1
            continue

        # Authoritative (or no authority declared): overwrite, but only bump
        # last_updated if something actually changed.
        prev_score = existing.get("score")
        scores[benchmark] = new_score_obj
        if prev_score != float(score):
            model_entry["last_updated"] = now
            overwrites += 1

    master["models"] = master_models
    master["generated_at"] = now
    master.setdefault("schema_version", "1")
    _write_json(MASTER_PATH, master)

    console.log(
        f"[normalize] resolved={resolved_records} additions={additions} "
        f"overwrites={overwrites} skipped_lower_source={skipped_lower_source} "
        f"unknowns_this_run={len(unknowns_this_run)}"
    )

    newly_flagged = _append_needs_review(list(unknowns_this_run.values()))
    console.log(f"[normalize] appended {newly_flagged} new names to needs_review.json")
    return newly_flagged


if __name__ == "__main__":
    normalize()
