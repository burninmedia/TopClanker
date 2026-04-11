"""
Behavioral tests for normalize.normalize().
"""

from __future__ import annotations

from normalize import normalize


def test_new_model_creates_entry_with_benchmark_type(scenario):
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": 88.7}],
    )
    new_count = normalize()
    assert new_count == 0

    master = scenario.load_master()
    entry = master["models"]["gpt-4o"]
    assert entry["display_name"] == "GPT-4o"
    assert entry["provider"] == "OpenAI"
    assert entry["first_seen"] == entry["last_updated"]

    score = entry["scores"]["mmlu"]
    assert score["score"] == 88.7
    assert score["source"] == "hf_leaderboard"
    assert score["benchmark_type"] == "knowledge"  # the apples-to-apples tag


def test_benchmark_types_propagate_for_every_known_benchmark(scenario):
    """Every benchmark in the registry should round-trip its type onto scores."""
    scenario.write_raw(
        "hf_leaderboard",
        [
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": 88.7},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "arc", "score": 96.0},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "hellaswag", "score": 95.1},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "gsm8k", "score": 92.0},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "winogrande", "score": 87.4},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "truthfulqa", "score": 70.0},
        ],
    )
    scenario.write_raw(
        "lmsys_arena",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "lmsys_elo", "score": 1287}],
    )
    normalize()

    scores = scenario.load_master()["models"]["gpt-4o"]["scores"]
    assert scores["mmlu"]["benchmark_type"] == "knowledge"
    assert scores["arc"]["benchmark_type"] == "reasoning"
    assert scores["hellaswag"]["benchmark_type"] == "commonsense"
    assert scores["gsm8k"]["benchmark_type"] == "math"
    assert scores["winogrande"]["benchmark_type"] == "commonsense"
    assert scores["truthfulqa"]["benchmark_type"] == "safety"
    assert scores["lmsys_elo"]["benchmark_type"] == "human_preference"


def test_alias_resolution_handles_multiple_formats(scenario):
    """HuggingFace-format, dated pin, and short name should all resolve to the
    same canonical_id."""
    scenario.write_raw(
        "hf_leaderboard",
        [
            {"model_raw_name": "openai/gpt-4o-2024-11-20", "benchmark": "mmlu", "score": 88.7},
            {"model_raw_name": "GPT-4o", "benchmark": "gsm8k", "score": 92.0},
            {"model_raw_name": "gpt-4o-2024-08-06", "benchmark": "arc", "score": 96.0},
        ],
    )
    normalize()

    master = scenario.load_master()
    assert list(master["models"].keys()) == ["gpt-4o"]
    scores = master["models"]["gpt-4o"]["scores"]
    assert set(scores.keys()) == {"mmlu", "gsm8k", "arc"}


def test_unknown_model_is_flagged_for_review(scenario):
    scenario.write_raw(
        "hf_leaderboard",
        [
            {"model_raw_name": "FakeVendor/Mystery-99B", "benchmark": "mmlu", "score": 50.0},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": 88.7},
        ],
    )
    new_count = normalize()
    assert new_count == 1

    review = scenario.load_needs_review()
    assert len(review["pending"]) == 1
    assert review["pending"][0]["raw_name"] == "FakeVendor/Mystery-99B"
    assert review["pending"][0]["source"] == "hf_leaderboard"

    # The known model still made it into master.
    assert "gpt-4o" in scenario.load_master()["models"]


def test_needs_review_deduplicates_across_runs(scenario):
    raw = [{"model_raw_name": "FakeVendor/Mystery-99B", "benchmark": "mmlu", "score": 50.0}]
    scenario.write_raw("hf_leaderboard", raw)
    assert normalize() == 1
    # Second run with the same unknown name -> not appended again.
    scenario.write_raw("hf_leaderboard", raw)
    assert normalize() == 0
    review = scenario.load_needs_review()
    assert len(review["pending"]) == 1


def test_authoritative_source_overwrites_previous_value(scenario):
    """mmlu's authoritative source is hf_leaderboard, so a second hf record
    should overwrite the first."""
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": 80.0}],
    )
    normalize()
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": 89.0}],
    )
    normalize()

    master = scenario.load_master()
    assert master["models"]["gpt-4o"]["scores"]["mmlu"]["score"] == 89.0


def test_non_authoritative_source_does_not_overwrite(scenario):
    """mmlu's authoritative source is hf_leaderboard. An lmsys record claiming
    mmlu must be ignored — the existing hf score wins."""
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": 88.7}],
    )
    normalize()
    scenario.write_raw(
        "lmsys_arena",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": 50.0}],
    )
    normalize()

    score = scenario.load_master()["models"]["gpt-4o"]["scores"]["mmlu"]
    assert score["score"] == 88.7
    assert score["source"] == "hf_leaderboard"


def test_existing_model_with_new_benchmark_is_added(scenario):
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": 88.7}],
    )
    normalize()
    scenario.write_raw(
        "lmsys_arena",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "lmsys_elo", "score": 1287}],
    )
    normalize()

    scores = scenario.load_master()["models"]["gpt-4o"]["scores"]
    assert scores["mmlu"]["score"] == 88.7
    assert scores["lmsys_elo"]["score"] == 1287.0
    assert scores["lmsys_elo"]["benchmark_type"] == "human_preference"


def test_lmsys_votes_metadata_is_carried_through(scenario):
    scenario.write_raw(
        "lmsys_arena",
        [
            {
                "model_raw_name": "openai/gpt-4o",
                "benchmark": "lmsys_elo",
                "score": 1287,
                "votes": 50000,
            }
        ],
    )
    normalize()
    score = scenario.load_master()["models"]["gpt-4o"]["scores"]["lmsys_elo"]
    assert score["votes"] == 50000


def test_records_with_missing_fields_are_skipped(scenario):
    scenario.write_raw(
        "hf_leaderboard",
        [
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": 88.7},
            {"benchmark": "mmlu", "score": 88.7},  # missing model
            {"model_raw_name": "openai/gpt-4o", "score": 88.7},  # missing benchmark
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu"},  # missing score
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu", "score": "abc"},  # bad score
        ],
    )
    normalize()
    master = scenario.load_master()
    assert master["models"]["gpt-4o"]["scores"]["mmlu"]["score"] == 88.7
    assert len(master["models"]["gpt-4o"]["scores"]) == 1


def test_unknown_benchmark_still_stored_without_type(scenario):
    """A benchmark not in benchmarks.json should still be persisted, just
    without a benchmark_type tag (since we don't know its category)."""
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "exotic_bench", "score": 42.0}],
    )
    normalize()
    score = scenario.load_master()["models"]["gpt-4o"]["scores"]["exotic_bench"]
    assert score["score"] == 42.0
    assert "benchmark_type" not in score
