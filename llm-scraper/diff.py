"""
Compute the site-facing weekly diff between the most recent archived master
snapshot and the freshly written master.json.

Each "updated" entry records per-benchmark deltas including `benchmark_type`
so the site can group changes apples-to-apples.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ARCHIVE_DIR = DATA_DIR / "archive"
MASTER_PATH = DATA_DIR / "master.json"
DIFF_PATH = DATA_DIR / "weekly_diff.json"

ARCHIVE_PATTERN = re.compile(r"^master_(\d{4}-\d{2}-\d{2})\.json$")

console = Console()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.log(f"[diff] WARNING: {path} is invalid JSON ({exc}); using default")
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _find_latest_archive() -> Path | None:
    if not ARCHIVE_DIR.exists():
        return None
    candidates: list[tuple[str, Path]] = []
    for path in ARCHIVE_DIR.glob("master_*.json"):
        match = ARCHIVE_PATTERN.match(path.name)
        if match:
            candidates.append((match.group(1), path))
    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0], reverse=True)
    return candidates[0][1]


def _empty_diff() -> dict[str, Any]:
    return {
        "diff_generated_at": None,
        "from_snapshot": None,
        "to_snapshot": None,
        "summary": {"models_added": 0, "models_updated": 0, "scores_changed": 0},
        "added": [],
        "updated": [],
        "removed": [],
    }


def compute_diff() -> dict[str, Any]:
    """
    Compare the latest archive to the current master.json and write weekly_diff.json.
    Returns the diff payload (also written to disk).
    """
    latest_archive_path = _find_latest_archive()

    # First run or no prior archive: write the stub diff and return.
    if latest_archive_path is None:
        console.log("[diff] no archive found — writing empty stub diff (first run)")
        diff = _empty_diff()
        diff["diff_generated_at"] = _now_iso()
        diff["to_snapshot"] = MASTER_PATH.name
        _write_json(DIFF_PATH, diff)
        return diff

    previous = _load_json(latest_archive_path, {"models": {}})
    current = _load_json(MASTER_PATH, {"models": {}})

    prev_models: dict[str, Any] = previous.get("models") or {}
    curr_models: dict[str, Any] = current.get("models") or {}

    prev_ids = set(prev_models.keys())
    curr_ids = set(curr_models.keys())

    added_ids = sorted(curr_ids - prev_ids)
    removed_ids = sorted(prev_ids - curr_ids)
    shared_ids = sorted(prev_ids & curr_ids)

    added_list: list[dict[str, Any]] = []
    for canonical_id in added_ids:
        entry = curr_models.get(canonical_id, {}) or {}
        added_list.append(
            {
                "canonical_id": canonical_id,
                "display_name": entry.get("display_name", canonical_id),
                "provider": entry.get("provider", "Unknown"),
            }
        )

    updated_list: list[dict[str, Any]] = []
    scores_changed_total = 0

    for canonical_id in shared_ids:
        prev_entry = prev_models.get(canonical_id, {}) or {}
        curr_entry = curr_models.get(canonical_id, {}) or {}
        prev_scores: dict[str, Any] = prev_entry.get("scores") or {}
        curr_scores: dict[str, Any] = curr_entry.get("scores") or {}

        changes: list[dict[str, Any]] = []
        all_bench_keys = set(prev_scores.keys()) | set(curr_scores.keys())
        for bench in sorted(all_bench_keys):
            prev_score_obj = prev_scores.get(bench) or {}
            curr_score_obj = curr_scores.get(bench) or {}
            prev_val = prev_score_obj.get("score") if isinstance(prev_score_obj, dict) else None
            curr_val = curr_score_obj.get("score") if isinstance(curr_score_obj, dict) else None

            if prev_val == curr_val:
                continue

            delta: float | None = None
            if isinstance(prev_val, (int, float)) and isinstance(curr_val, (int, float)):
                delta = round(float(curr_val) - float(prev_val), 3)

            change: dict[str, Any] = {
                "benchmark": bench,
                "old_score": prev_val,
                "new_score": curr_val,
                "delta": delta,
            }
            # Propagate benchmark_type for apples-to-apples grouping on the site.
            bench_type = (
                curr_score_obj.get("benchmark_type")
                if isinstance(curr_score_obj, dict)
                else None
            ) or (
                prev_score_obj.get("benchmark_type")
                if isinstance(prev_score_obj, dict)
                else None
            )
            if bench_type:
                change["benchmark_type"] = bench_type

            changes.append(change)

        if changes:
            updated_list.append(
                {
                    "canonical_id": canonical_id,
                    "display_name": curr_entry.get("display_name", canonical_id),
                    "changes": changes,
                }
            )
            scores_changed_total += len(changes)

    removed_list: list[dict[str, Any]] = []
    for canonical_id in removed_ids:
        entry = prev_models.get(canonical_id, {}) or {}
        removed_list.append(
            {
                "canonical_id": canonical_id,
                "display_name": entry.get("display_name", canonical_id),
                "provider": entry.get("provider", "Unknown"),
            }
        )

    diff = {
        "diff_generated_at": _now_iso(),
        "from_snapshot": latest_archive_path.name,
        "to_snapshot": MASTER_PATH.name,
        "summary": {
            "models_added": len(added_list),
            "models_updated": len(updated_list),
            "scores_changed": scores_changed_total,
        },
        "added": added_list,
        "updated": updated_list,
        "removed": removed_list,
    }

    _write_json(DIFF_PATH, diff)
    console.log(
        f"[diff] added={len(added_list)} updated={len(updated_list)} "
        f"scores_changed={scores_changed_total} removed={len(removed_list)}"
    )
    return diff


if __name__ == "__main__":
    compute_diff()
