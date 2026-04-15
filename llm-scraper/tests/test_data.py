"""
Schema-style sanity checks on the tracked registries themselves. These guard
against accidental edits that would break the pipeline at runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

ALLOWED_BENCHMARK_TYPES = {
    "knowledge",
    "reasoning",
    "commonsense",
    "math",
    "safety",
    "human_preference",
    "instruction_following",
}


def _load(name: str) -> dict:
    return json.loads((DATA / name).read_text())


def test_benchmarks_have_required_fields():
    benchmarks = _load("benchmarks.json")
    assert benchmarks, "benchmarks.json is empty"
    for key, entry in benchmarks.items():
        assert "display_name" in entry, f"{key}: missing display_name"
        assert "scale" in entry, f"{key}: missing scale"
        assert "higher_is_better" in entry, f"{key}: missing higher_is_better"
        assert "authoritative_source" in entry, f"{key}: missing authoritative_source"
        assert "benchmark_type" in entry, f"{key}: missing benchmark_type"


def test_benchmark_types_are_in_allowed_set():
    benchmarks = _load("benchmarks.json")
    for key, entry in benchmarks.items():
        bt = entry["benchmark_type"]
        assert bt in ALLOWED_BENCHMARK_TYPES, (
            f"{key}: benchmark_type {bt!r} not in {sorted(ALLOWED_BENCHMARK_TYPES)}"
        )


def test_models_have_required_fields():
    models = _load("models.json")
    assert models, "models.json is empty"
    for key, entry in models.items():
        assert "canonical_id" in entry, f"{key}: missing canonical_id"
        assert "display_name" in entry, f"{key}: missing display_name"
        assert "provider" in entry, f"{key}: missing provider"
        assert "aliases" in entry, f"{key}: missing aliases"
        assert isinstance(entry["aliases"], list), f"{key}: aliases must be a list"
        assert entry["aliases"], f"{key}: aliases is empty"


def test_no_duplicate_canonical_ids():
    models = _load("models.json")
    ids = [v["canonical_id"] for v in models.values()]
    assert len(ids) == len(set(ids)), f"duplicate canonical_id values: {ids}"


def test_aliases_are_unique_within_each_model():
    models = _load("models.json")
    for key, entry in models.items():
        aliases = entry["aliases"]
        assert len(aliases) == len(set(aliases)), f"{key}: duplicate aliases {aliases}"


def test_aliases_do_not_collide_across_models_case_insensitive():
    """If two different canonical models share an alias, normalize would route
    raw scores to whichever was loaded last. That's a bug — fail loudly."""
    models = _load("models.json")
    seen: dict[str, str] = {}
    for key, entry in models.items():
        for alias in entry["aliases"]:
            normalized = alias.strip().lower()
            if normalized in seen and seen[normalized] != entry["canonical_id"]:
                raise AssertionError(
                    f"alias {alias!r} maps to both {seen[normalized]} and {entry['canonical_id']}"
                )
            seen[normalized] = entry["canonical_id"]


def test_stub_data_files_are_valid_json():
    for name in ("master.json", "weekly_diff.json", "needs_review.json"):
        json.loads((DATA / name).read_text())  # raises if malformed
