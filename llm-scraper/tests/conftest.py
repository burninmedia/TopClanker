"""
Shared fixtures for the llm-scraper test suite.

The pipeline modules (normalize, diff, run) all hold their working paths as
module-level constants computed at import time. To run them against an
isolated temp directory, every test patches each of those constants to point
at the per-test tmp_path. The `scenario` fixture below does that wiring once
and exposes a small helper API for writing fake raw scraper files and
loading the resulting artifacts.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

import diff
import normalize
import run

REPO_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _stub_master() -> dict[str, Any]:
    return {"generated_at": None, "schema_version": "1", "models": {}}


def _stub_needs_review() -> dict[str, Any]:
    return {"last_updated": None, "pending": []}


def _stub_diff() -> dict[str, Any]:
    return {
        "diff_generated_at": None,
        "from_snapshot": None,
        "to_snapshot": None,
        "summary": {"models_added": 0, "models_updated": 0, "scores_changed": 0},
        "added": [],
        "updated": [],
        "removed": [],
    }


@dataclass
class Scenario:
    """Handle to an isolated temp data tree."""

    root: Path
    data_dir: Path
    raw_dir: Path
    archive_dir: Path
    master_path: Path
    diff_path: Path
    needs_review_path: Path
    benchmarks_path: Path
    models_path: Path

    def write_raw(self, source: str, records: list[dict]) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": source,
            "scraped_at": "2025-01-12T00:00:00Z",
            "records": records,
        }
        (self.raw_dir / f"{source}.json").write_text(json.dumps(payload))

    def write_master(self, master: dict[str, Any]) -> None:
        self.master_path.write_text(json.dumps(master))

    def write_archive(self, date: str, master: dict[str, Any]) -> Path:
        path = self.archive_dir / f"master_{date}.json"
        path.write_text(json.dumps(master))
        return path

    def load_master(self) -> dict[str, Any]:
        return json.loads(self.master_path.read_text())

    def load_diff(self) -> dict[str, Any]:
        return json.loads(self.diff_path.read_text())

    def load_needs_review(self) -> dict[str, Any]:
        return json.loads(self.needs_review_path.read_text())


@pytest.fixture
def scenario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Scenario:
    """
    Build an isolated temp data tree mirroring `llm-scraper/data/`, with the
    real benchmarks.json and models.json copied in plus stub master /
    weekly_diff / needs_review files. Patch every module-level path constant
    in normalize, diff, and run so the pipeline writes only into tmp_path.
    """
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    archive_dir = data_dir / "archive"
    data_dir.mkdir(parents=True)
    raw_dir.mkdir()
    archive_dir.mkdir()

    benchmarks_path = data_dir / "benchmarks.json"
    models_path = data_dir / "models.json"
    master_path = data_dir / "master.json"
    diff_path = data_dir / "weekly_diff.json"
    needs_review_path = data_dir / "needs_review.json"

    # Real registries — alias and benchmark metadata stays realistic.
    shutil.copy(REPO_DATA_DIR / "benchmarks.json", benchmarks_path)
    shutil.copy(REPO_DATA_DIR / "models.json", models_path)

    master_path.write_text(json.dumps(_stub_master()))
    needs_review_path.write_text(json.dumps(_stub_needs_review()))
    diff_path.write_text(json.dumps(_stub_diff()))

    # --- normalize module ---
    monkeypatch.setattr(normalize, "DATA_DIR", data_dir)
    monkeypatch.setattr(normalize, "RAW_DIR", raw_dir)
    monkeypatch.setattr(normalize, "BENCHMARKS_PATH", benchmarks_path)
    monkeypatch.setattr(normalize, "MODELS_PATH", models_path)
    monkeypatch.setattr(normalize, "MASTER_PATH", master_path)
    monkeypatch.setattr(normalize, "NEEDS_REVIEW_PATH", needs_review_path)

    # --- diff module ---
    monkeypatch.setattr(diff, "DATA_DIR", data_dir)
    monkeypatch.setattr(diff, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(diff, "MASTER_PATH", master_path)
    monkeypatch.setattr(diff, "DIFF_PATH", diff_path)

    # --- run module ---
    monkeypatch.setattr(run, "SCRIPT_DIR", tmp_path)
    monkeypatch.setattr(run, "DATA_DIR", data_dir)
    monkeypatch.setattr(run, "RAW_DIR", raw_dir)
    monkeypatch.setattr(run, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(run, "MASTER_PATH", master_path)
    monkeypatch.setattr(run, "BENCHMARKS_PATH", benchmarks_path)
    monkeypatch.setattr(run, "EXIT_CODE_PATH", tmp_path / ".pipeline_exit_code")
    monkeypatch.setattr(run, "SUMMARY_PATH", tmp_path / ".pipeline_summary")
    monkeypatch.setattr(run, "NEEDS_REVIEW_NEW_PATH", tmp_path / ".needs_review_new")

    return Scenario(
        root=tmp_path,
        data_dir=data_dir,
        raw_dir=raw_dir,
        archive_dir=archive_dir,
        master_path=master_path,
        diff_path=diff_path,
        needs_review_path=needs_review_path,
        benchmarks_path=benchmarks_path,
        models_path=models_path,
    )
