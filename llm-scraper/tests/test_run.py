"""
Tests for the orchestrator: archive behavior, exit codes, and the temp files
GitHub Actions consumes.
"""

from __future__ import annotations

import json

import pytest

import run
from scrapers import hf_leaderboard, lmsys_arena


def _patch_scrapers(monkeypatch, scenario, hf_records, lmsys_records, hf_ok=True, lmsys_ok=True):
    def fake_hf():
        scenario.write_raw("hf_leaderboard", hf_records)
        return hf_ok

    def fake_lmsys():
        scenario.write_raw("lmsys_arena", lmsys_records)
        return lmsys_ok

    monkeypatch.setattr(hf_leaderboard, "run_scraper", fake_hf)
    monkeypatch.setattr(lmsys_arena, "run_scraper", fake_lmsys)


def test_clean_run_returns_exit_code_zero(scenario, monkeypatch):
    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 88.7}],
        lmsys_records=[],
    )
    rc = run.main()
    assert rc == 0
    assert (scenario.root / ".pipeline_exit_code").read_text().strip() == "0"


def test_unknown_model_returns_exit_code_two(scenario, monkeypatch):
    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 88.7},
            {"model_raw_name": "Surprise/Unknown-99B", "benchmark": "mmlu_pro", "score": 50.0},
        ],
        lmsys_records=[],
    )
    rc = run.main()
    assert rc == 2
    assert (scenario.root / ".pipeline_exit_code").read_text().strip() == "2"
    new_review = (scenario.root / ".needs_review_new").read_text().strip()
    assert new_review == "Surprise/Unknown-99B"


def test_archive_skipped_on_empty_stub_first_run(scenario, monkeypatch):
    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 88.7}],
        lmsys_records=[],
    )
    run.main()
    assert list(scenario.archive_dir.glob("master_*.json")) == []


def test_archive_created_on_second_run_after_master_populated(scenario, monkeypatch):
    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 88.0}],
        lmsys_records=[],
    )
    run.main()
    assert list(scenario.archive_dir.glob("master_*.json")) == []  # first run skipped

    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 89.0}],
        lmsys_records=[],
    )
    run.main()
    archives = list(scenario.archive_dir.glob("master_*.json"))
    assert len(archives) == 1


def test_archive_idempotent_when_run_twice_in_one_day(scenario, monkeypatch):
    """Archive on day-N+1 creates one file. Re-running the same day should
    NOT overwrite or create a second archive — re-run protection."""
    # Seed master so the next run actually has something to archive.
    scenario.write_master(
        {
            "generated_at": "2025-01-12T00:00:00Z",
            "schema_version": "1",
            "models": {
                "gpt-4o": {
                    "display_name": "GPT-4o",
                    "provider": "OpenAI",
                    "first_seen": "2025-01-12T00:00:00Z",
                    "last_updated": "2025-01-12T00:00:00Z",
                    "scores": {
                        "mmlu_pro": {
                            "score": 60.0,
                            "source": "hf_leaderboard",
                            "benchmark_type": "knowledge",
                            "recorded_at": "2025-01-12T00:00:00Z",
                        }
                    },
                }
            },
        }
    )

    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 89.0}],
        lmsys_records=[],
    )
    run.main()
    first = sorted(p.name for p in scenario.archive_dir.glob("master_*.json"))
    assert len(first) == 1

    # Capture the contents of the archive after run 1.
    archive_path = scenario.archive_dir / first[0]
    archive_after_run_1 = archive_path.read_text()

    # Re-run on the same day. Master changes, but archive should be untouched.
    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 95.0}],
        lmsys_records=[],
    )
    run.main()
    second = sorted(p.name for p in scenario.archive_dir.glob("master_*.json"))
    assert second == first
    assert archive_path.read_text() == archive_after_run_1


def test_summary_file_format_is_plain_text(scenario, monkeypatch):
    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 88.7},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "math_lvl5", "score": 38.2},
        ],
        lmsys_records=[
            {"model_raw_name": "openai/gpt-4o", "benchmark": "lmsys_elo", "score": 1287}
        ],
    )
    run.main()

    text = (scenario.root / ".pipeline_summary").read_text()
    assert "Models added:" in text
    assert "Models updated:" in text
    assert "Scores changed:" in text
    assert "Flagged for review:" in text
    assert "Sources:" in text
    assert "hf_leaderboard" in text
    assert "lmsys_arena" in text
    # No markdown control chars
    assert "**" not in text
    assert "##" not in text


def test_no_new_review_writes_None_to_needs_review_new(scenario, monkeypatch):
    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 88.7}],
        lmsys_records=[],
    )
    run.main()
    body = (scenario.root / ".needs_review_new").read_text().strip()
    assert body == "None"


def test_pre_existing_needs_review_entries_are_not_listed_as_new(scenario, monkeypatch):
    """If needs_review.json already has an entry from a previous run, and the
    same name shows up again this run, .needs_review_new should NOT include
    it (and the exit code should be 0, not 2)."""
    # Pre-seed needs_review with an old entry.
    scenario.needs_review_path.write_text(
        json.dumps(
            {
                "last_updated": "2025-01-05T00:00:00Z",
                "pending": [
                    {
                        "raw_name": "OldVendor/Old-Model",
                        "source": "hf_leaderboard",
                        "first_seen": "2025-01-05T00:00:00Z",
                    }
                ],
            }
        )
    )

    _patch_scrapers(
        monkeypatch,
        scenario,
        hf_records=[
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 88.7},
            {"model_raw_name": "OldVendor/Old-Model", "benchmark": "mmlu_pro", "score": 50.0},
        ],
        lmsys_records=[],
    )
    rc = run.main()

    assert rc == 0  # nothing NEW was added this run
    assert (scenario.root / ".needs_review_new").read_text().strip() == "None"
    # And the existing entry is still in the queue, not duplicated.
    review = scenario.load_needs_review()
    assert len(review["pending"]) == 1


def test_scraper_failure_propagates_into_summary_errors(scenario, monkeypatch):
    """If hf_leaderboard.run_scraper() returns False, the summary table should
    show errors=1 for that source even though the pipeline overall succeeds."""

    def fake_hf():
        scenario.write_raw("hf_leaderboard", [])  # empty stub
        return False

    def fake_lmsys():
        scenario.write_raw(
            "lmsys_arena",
            [{"model_raw_name": "openai/gpt-4o", "benchmark": "lmsys_elo", "score": 1287}],
        )
        return True

    monkeypatch.setattr(hf_leaderboard, "run_scraper", fake_hf)
    monkeypatch.setattr(lmsys_arena, "run_scraper", fake_lmsys)

    rc = run.main()
    assert rc == 0  # not a hard failure, just a soft error
    text = (scenario.root / ".pipeline_summary").read_text()
    assert "hf_leaderboard" in text
    assert "1 error" in text  # singular form for 1
