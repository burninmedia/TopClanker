"""
Orchestrator: archive -> scrape -> normalize -> diff -> report.

Exit codes (also written to .pipeline_exit_code at repo-root level for CI):
  0 = success, all names resolved cleanly
  2 = success, but new names were flagged for human review this run
  1 = hard failure (also sys.exit(1))
"""

from __future__ import annotations

import json
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from rich.console import Console
from rich.table import Table

# Make sibling modules importable whether run from repo root or llm-scraper/.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from diff import compute_diff  # noqa: E402
from normalize import normalize  # noqa: E402
from scrapers import hf_leaderboard, lmsys_arena  # noqa: E402

DATA_DIR = SCRIPT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
ARCHIVE_DIR = DATA_DIR / "archive"
MASTER_PATH = DATA_DIR / "master.json"
BENCHMARKS_PATH = DATA_DIR / "benchmarks.json"

# Temp files for GitHub Actions consumption. Per spec, these live at the repo
# root — i.e. the parent of llm-scraper/ when the pipeline is run as-is.
REPO_ROOT = SCRIPT_DIR.parent
EXIT_CODE_PATH = REPO_ROOT / ".pipeline_exit_code"
SUMMARY_PATH = REPO_ROOT / ".pipeline_summary"
NEEDS_REVIEW_NEW_PATH = REPO_ROOT / ".needs_review_new"

console = Console()


def _now_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def _archive_current_master() -> None:
    """
    Copy the current master.json into data/archive/master_YYYY-MM-DD.json.
    Skip if master.json is the empty stub (no models) or the archive file
    for today already exists (re-run protection).
    """
    if not MASTER_PATH.exists():
        console.log("[run] no master.json present — nothing to archive")
        return

    master = _load_json(MASTER_PATH, {})
    models = master.get("models") or {}
    if not models:
        console.log("[run] master.json is the empty stub — skipping archive")
        return

    archive_name = f"master_{_now_date()}.json"
    archive_path = ARCHIVE_DIR / archive_name
    if archive_path.exists():
        console.log(f"[run] archive {archive_name} already exists — skipping (re-run protection)")
        return

    shutil.copy2(MASTER_PATH, archive_path)
    console.log(f"[run] archived master.json -> {archive_path}")


def _run_scrapers() -> dict[str, bool]:
    """Call each scraper's run_scraper(); collect outcomes. Never raises."""
    scrapers: list[tuple[str, Callable[[], bool]]] = [
        ("hf_leaderboard", hf_leaderboard.run_scraper),
        ("lmsys_arena", lmsys_arena.run_scraper),
    ]
    results: dict[str, bool] = {}
    for name, fn in scrapers:
        try:
            console.log(f"[run] scraper[{name}] starting")
            ok = bool(fn())
        except Exception as exc:  # noqa: BLE001 — defensive, scrapers shouldn't raise
            console.log(f"[run] scraper[{name}] raised unexpectedly: {exc!r}")
            ok = False
        results[name] = ok
        console.log(f"[run] scraper[{name}] -> {'OK' if ok else 'FAIL'}")
    return results


def _source_stats() -> dict[str, dict[str, int]]:
    """
    Inspect data/raw/*.json and return per-source stats:
      {source: {"models": N, "benchmarks": N, "errors": 0|1}}.
    """
    stats: dict[str, dict[str, int]] = {}
    for path in sorted(RAW_DIR.glob("*.json")):
        payload = _load_json(path, None)
        source = path.stem
        if not isinstance(payload, dict):
            stats[source] = {"models": 0, "benchmarks": 0, "errors": 1}
            continue
        records = payload.get("records") or []
        if not isinstance(records, list):
            stats[source] = {"models": 0, "benchmarks": 0, "errors": 1}
            continue
        models = {
            r.get("model_raw_name")
            for r in records
            if isinstance(r, dict) and isinstance(r.get("model_raw_name"), str)
        }
        benchmarks = {
            r.get("benchmark")
            for r in records
            if isinstance(r, dict) and isinstance(r.get("benchmark"), str)
        }
        stats[source] = {
            "models": len(models),
            "benchmarks": len(benchmarks),
            "errors": 0,
        }
    return stats


def _print_summary_table(
    source_stats: dict[str, dict[str, int]],
    scraper_results: dict[str, bool],
    diff_summary: dict[str, int],
    new_review_count: int,
) -> None:
    table = Table(title="LLM Benchmark Scrape Summary")
    table.add_column("Source")
    table.add_column("Models Found", justify="right")
    table.add_column("Benchmarks", justify="right")
    table.add_column("Errors", justify="right")

    # Ensure every source that we tried to run shows a row, even on total failure.
    all_sources = sorted(set(list(source_stats.keys()) + list(scraper_results.keys())))
    for source in all_sources:
        stats = source_stats.get(source, {"models": 0, "benchmarks": 0, "errors": 0})
        errors = stats["errors"]
        if source in scraper_results and not scraper_results[source]:
            errors = max(errors, 1)
        table.add_row(
            source,
            str(stats["models"]),
            str(stats["benchmarks"]),
            str(errors),
        )

    console.print(table)
    console.print(
        f"Models added: {diff_summary.get('models_added', 0)} | "
        f"Models updated: {diff_summary.get('models_updated', 0)} | "
        f"Scores changed: {diff_summary.get('scores_changed', 0)}"
    )
    if new_review_count:
        console.print(
            f"[yellow]Flagged for review: {new_review_count} new names in needs_review.json[/yellow]"
        )
    else:
        console.print("Flagged for review: 0 new names")


def _format_summary_text(
    source_stats: dict[str, dict[str, int]],
    scraper_results: dict[str, bool],
    diff_summary: dict[str, int],
    new_review_count: int,
) -> str:
    lines: list[str] = []
    lines.append(f"Models added: {diff_summary.get('models_added', 0)}")
    lines.append(f"Models updated: {diff_summary.get('models_updated', 0)}")
    lines.append(f"Scores changed: {diff_summary.get('scores_changed', 0)}")
    lines.append(f"Flagged for review: {new_review_count} new names")
    lines.append("")
    lines.append("Sources:")

    all_sources = sorted(set(list(source_stats.keys()) + list(scraper_results.keys())))
    name_width = max((len(s) for s in all_sources), default=10)
    for source in all_sources:
        stats = source_stats.get(source, {"models": 0, "benchmarks": 0, "errors": 0})
        errors = stats["errors"]
        if source in scraper_results and not scraper_results[source]:
            errors = max(errors, 1)
        bench_word = "benchmark" if stats["benchmarks"] == 1 else "benchmarks"
        err_word = "error" if errors == 1 else "errors"
        lines.append(
            f"{source.ljust(name_width)} | {stats['models']:>3} models "
            f"| {stats['benchmarks']} {bench_word} | {errors} {err_word}"
        )
    return "\n".join(lines) + "\n"


def _write_temp_files(
    exit_code: int,
    summary_text: str,
    new_review_names: list[str],
) -> None:
    EXIT_CODE_PATH.write_text(str(exit_code), encoding="utf-8")
    SUMMARY_PATH.write_text(summary_text, encoding="utf-8")
    body = "\n".join(new_review_names) if new_review_names else "None"
    NEEDS_REVIEW_NEW_PATH.write_text(body + "\n", encoding="utf-8")


def _collect_new_review_names_from_needs_review(baseline_names: set[str]) -> list[str]:
    """
    Return the raw_names that appeared in needs_review.json after the run
    but were not present in the baseline snapshot taken before normalize().
    """
    current = _load_json(DATA_DIR / "needs_review.json", {"pending": []})
    pending = current.get("pending", []) or []
    new_names: list[str] = []
    for entry in pending:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("raw_name")
        if isinstance(raw, str) and raw not in baseline_names:
            new_names.append(raw)
    return new_names


def main() -> int:
    try:
        # Step 1: directories
        _ensure_dirs()

        # Step 2: archive current master.json (if non-empty)
        _archive_current_master()

        # Step 3: run scrapers
        scraper_results = _run_scrapers()

        # Capture needs_review baseline before normalize mutates it, so we
        # can surface ONLY the names newly added by this run.
        baseline = _load_json(DATA_DIR / "needs_review.json", {"pending": []})
        baseline_names: set[str] = {
            entry.get("raw_name")
            for entry in (baseline.get("pending") or [])
            if isinstance(entry, dict) and isinstance(entry.get("raw_name"), str)
        }

        # Step 4: normalize
        new_review_count = normalize()

        # Step 5: diff
        diff_payload = compute_diff()
        diff_summary = diff_payload.get("summary", {}) or {}

        # Step 6: rich summary table
        source_stats = _source_stats()
        _print_summary_table(source_stats, scraper_results, diff_summary, new_review_count)

        # Step 7: temp files for Actions
        summary_text = _format_summary_text(
            source_stats, scraper_results, diff_summary, new_review_count
        )
        new_review_names = _collect_new_review_names_from_needs_review(baseline_names)
        exit_code = 2 if new_review_count > 0 else 0
        _write_temp_files(exit_code, summary_text, new_review_names)

        console.log(f"[run] pipeline complete — exit code {exit_code}")
        return exit_code

    except Exception:  # noqa: BLE001 — last-resort; turn into hard failure
        console.log("[run] HARD FAILURE:")
        console.print(traceback.format_exc())
        try:
            EXIT_CODE_PATH.write_text("1", encoding="utf-8")
            SUMMARY_PATH.write_text("Pipeline hard-failed. See workflow logs.\n", encoding="utf-8")
            NEEDS_REVIEW_NEW_PATH.write_text("None\n", encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
