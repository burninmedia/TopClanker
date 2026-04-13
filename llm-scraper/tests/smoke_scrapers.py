#!/usr/bin/env python
"""
Live smoke test: call each scraper against the real APIs and report what was
captured. Produces a Markdown report to scraper_smoke_results.md (for
$GITHUB_STEP_SUMMARY) and also prints it to stdout.

This intentionally does NOT fail the build if a source is unreachable — the
unit tests are the hard gate. This script is advisory: it lets the reviewer
confirm the scrapers still parse real data correctly.

Exit codes:
  0 = at least one scraper returned data
  1 = every scraper returned 0 records (likely broken)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make sibling modules importable.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scrapers import hf_leaderboard, lmsys_arena  # noqa: E402

REPORT_PATH = PROJECT_DIR / "scraper_smoke_results.md"


def _summarize_source(name: str, output_path: Path, ok: bool) -> dict:
    if not output_path.exists():
        return {
            "name": name,
            "ok": False,
            "record_count": 0,
            "model_count": 0,
            "benchmark_count": 0,
            "benchmarks": [],
            "sample_models": [],
            "sample_records": [],
        }

    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "name": name,
            "ok": False,
            "record_count": 0,
            "model_count": 0,
            "benchmark_count": 0,
            "benchmarks": [],
            "sample_models": [],
            "sample_records": [],
        }

    records = data.get("records") or []
    models = sorted(
        {r["model_raw_name"] for r in records if isinstance(r, dict) and "model_raw_name" in r}
    )
    benchmarks = sorted(
        {r["benchmark"] for r in records if isinstance(r, dict) and "benchmark" in r}
    )
    return {
        "name": name,
        "ok": ok and len(records) > 0,
        "record_count": len(records),
        "model_count": len(models),
        "benchmark_count": len(benchmarks),
        "benchmarks": benchmarks,
        "sample_models": models[:15],
        "sample_records": records[:5],
    }


def _build_report(results: list[dict]) -> str:
    lines: list[str] = []
    lines.append("## Scraper Smoke Test Results\n")

    # Overview table
    lines.append("| Source | Status | Models | Benchmarks | Records |")
    lines.append("|--------|--------|-------:|----------:|---------:|")
    for r in results:
        if r["ok"]:
            status = "pass"
        elif r["record_count"] > 0:
            status = "warn"
        else:
            status = "FAIL"
        lines.append(
            f"| `{r['name']}` | {status} | {r['model_count']} "
            f"| {r['benchmark_count']} | {r['record_count']} |"
        )
    lines.append("")

    # Per-source details
    for r in results:
        lines.append(f"### {r['name']}\n")

        if not r["ok"] and r["record_count"] == 0:
            lines.append(
                "> Scraper returned 0 records. The upstream API may be "
                "unavailable, or the parser needs updating.\n"
            )
            continue

        if r["benchmarks"]:
            lines.append(f"**Benchmarks captured:** `{'`, `'.join(r['benchmarks'])}`\n")

        if r["sample_models"]:
            shown = len(r["sample_models"])
            total = r["model_count"]
            lines.append(
                f"**Sample models** (showing {shown} of {total}):\n"
            )
            for m in r["sample_models"]:
                lines.append(f"- `{m}`")
            lines.append("")

        if r["sample_records"]:
            lines.append("<details>")
            lines.append("<summary>Sample records (first 5)</summary>\n")
            lines.append("```json")
            lines.append(json.dumps(r["sample_records"], indent=2))
            lines.append("```\n")
            lines.append("</details>\n")

    # Footer
    any_ok = any(r["ok"] for r in results)
    if not any_ok:
        lines.append(
            "> **All scrapers returned 0 records.** This may indicate a "
            "network issue or an upstream API change that needs a parser fix.\n"
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    # Ensure runtime dirs exist.
    (PROJECT_DIR / "data" / "raw").mkdir(parents=True, exist_ok=True)

    scrapers = [
        ("hf_leaderboard", hf_leaderboard.run_scraper, hf_leaderboard.OUTPUT_PATH),
        ("lmsys_arena", lmsys_arena.run_scraper, lmsys_arena.OUTPUT_PATH),
    ]

    results: list[dict] = []
    for name, fn, output_path in scrapers:
        try:
            ok = bool(fn())
        except Exception:
            ok = False
        results.append(_summarize_source(name, output_path, ok))

    report = _build_report(results)

    # Write the markdown file for GITHUB_STEP_SUMMARY.
    REPORT_PATH.write_text(report, encoding="utf-8")

    # Also print so it shows in the CI log.
    print(report)

    any_ok = any(r["ok"] for r in results)
    return 0 if any_ok else 1


if __name__ == "__main__":
    sys.exit(main())
