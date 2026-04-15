"""
Behavioral tests for normalize.normalize().
"""

from __future__ import annotations

from normalize import normalize


def test_new_model_creates_entry_with_benchmark_type(scenario):
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 66.3}],
    )
    new_count = normalize()
    assert new_count == 0

    master = scenario.load_master()
    entry = master["models"]["gpt-4o"]
    assert entry["display_name"] == "GPT-4o"
    assert entry["provider"] == "OpenAI"
    assert entry["first_seen"] == entry["last_updated"]

    score = entry["scores"]["mmlu_pro"]
    assert score["score"] == 66.3
    assert score["source"] == "hf_leaderboard"
    assert score["benchmark_type"] == "knowledge"  # the apples-to-apples tag


def test_benchmark_types_propagate_for_every_known_benchmark(scenario):
    """Every benchmark in the registry should round-trip its type onto scores."""
    scenario.write_raw(
        "hf_leaderboard",
        [
            {"model_raw_name": "openai/gpt-4o", "benchmark": "ifeval", "score": 82.1},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "bbh", "score": 55.4},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "math_lvl5", "score": 38.2},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "gpqa", "score": 14.0},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "musr", "score": 18.8},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 66.3},
        ],
    )
    scenario.write_raw(
        "lmsys_arena",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "lmsys_elo", "score": 1287}],
    )
    normalize()

    scores = scenario.load_master()["models"]["gpt-4o"]["scores"]
    assert scores["ifeval"]["benchmark_type"] == "instruction_following"
    assert scores["bbh"]["benchmark_type"] == "reasoning"
    assert scores["math_lvl5"]["benchmark_type"] == "math"
    assert scores["gpqa"]["benchmark_type"] == "knowledge"
    assert scores["musr"]["benchmark_type"] == "reasoning"
    assert scores["mmlu_pro"]["benchmark_type"] == "knowledge"
    assert scores["lmsys_elo"]["benchmark_type"] == "human_preference"


def test_alias_resolution_handles_multiple_formats(scenario):
    """HuggingFace-format, dated pin, and short name should all resolve to the
    same canonical_id."""
    scenario.write_raw(
        "hf_leaderboard",
        [
            {"model_raw_name": "openai/gpt-4o-2024-11-20", "benchmark": "mmlu_pro", "score": 66.3},
            {"model_raw_name": "GPT-4o", "benchmark": "math_lvl5", "score": 38.2},
            {"model_raw_name": "gpt-4o-2024-08-06", "benchmark": "bbh", "score": 55.4},
        ],
    )
    normalize()

    master = scenario.load_master()
    assert list(master["models"].keys()) == ["gpt-4o"]
    scores = master["models"]["gpt-4o"]["scores"]
    assert set(scores.keys()) == {"mmlu_pro", "math_lvl5", "bbh"}


def test_unknown_model_is_flagged_for_review(scenario):
    scenario.write_raw(
        "hf_leaderboard",
        [
            {"model_raw_name": "FakeVendor/Mystery-99B", "benchmark": "mmlu_pro", "score": 50.0},
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 66.3},
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
    raw = [{"model_raw_name": "FakeVendor/Mystery-99B", "benchmark": "mmlu_pro", "score": 50.0}]
    scenario.write_raw("hf_leaderboard", raw)
    assert normalize() == 1
    # Second run with the same unknown name -> not appended again.
    scenario.write_raw("hf_leaderboard", raw)
    assert normalize() == 0
    review = scenario.load_needs_review()
    assert len(review["pending"]) == 1


def test_authoritative_source_overwrites_previous_value(scenario):
    """mmlu_pro's authoritative source is hf_leaderboard, so a second hf
    record should overwrite the first."""
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 60.0}],
    )
    normalize()
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 66.3}],
    )
    normalize()

    master = scenario.load_master()
    assert master["models"]["gpt-4o"]["scores"]["mmlu_pro"]["score"] == 66.3


def test_non_authoritative_source_does_not_overwrite(scenario):
    """mmlu_pro's authoritative source is hf_leaderboard. An lmsys record
    claiming mmlu_pro must be ignored — the existing hf score wins."""
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 66.3}],
    )
    normalize()
    scenario.write_raw(
        "lmsys_arena",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 50.0}],
    )
    normalize()

    score = scenario.load_master()["models"]["gpt-4o"]["scores"]["mmlu_pro"]
    assert score["score"] == 66.3
    assert score["source"] == "hf_leaderboard"


def test_existing_model_with_new_benchmark_is_added(scenario):
    scenario.write_raw(
        "hf_leaderboard",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 66.3}],
    )
    normalize()
    scenario.write_raw(
        "lmsys_arena",
        [{"model_raw_name": "openai/gpt-4o", "benchmark": "lmsys_elo", "score": 1287}],
    )
    normalize()

    scores = scenario.load_master()["models"]["gpt-4o"]["scores"]
    assert scores["mmlu_pro"]["score"] == 66.3
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
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": 66.3},
            {"benchmark": "mmlu_pro", "score": 66.3},  # missing model
            {"model_raw_name": "openai/gpt-4o", "score": 66.3},  # missing benchmark
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro"},  # missing score
            {"model_raw_name": "openai/gpt-4o", "benchmark": "mmlu_pro", "score": "abc"},  # bad score
        ],
    )
    normalize()
    master = scenario.load_master()
    assert master["models"]["gpt-4o"]["scores"]["mmlu_pro"]["score"] == 66.3
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
