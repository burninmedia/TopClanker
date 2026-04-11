"""
Pure-function tests for scraper helpers. No network. The high-level
`run_scraper()` entry points are exercised indirectly via test_run.py with
monkeypatched stand-ins.
"""

from __future__ import annotations

from scrapers import hf_leaderboard, lmsys_arena


# ---------- hf_leaderboard helpers ----------


def test_hf_coerce_score_zero_to_one_range_scaled_to_percent():
    assert hf_leaderboard._coerce_score(0.887) == 88.7
    assert hf_leaderboard._coerce_score(0.5) == 50.0
    assert hf_leaderboard._coerce_score(1.0) == 100.0


def test_hf_coerce_score_already_percent_passes_through():
    assert hf_leaderboard._coerce_score(85.4) == 85.4
    assert hf_leaderboard._coerce_score(99.99) == 99.99


def test_hf_coerce_score_invalid_returns_none():
    assert hf_leaderboard._coerce_score("not a number") is None
    assert hf_leaderboard._coerce_score(None) is None
    assert hf_leaderboard._coerce_score({}) is None


def test_hf_map_column_canonical_lookup():
    assert hf_leaderboard._map_column_to_benchmark("MMLU") == "mmlu"
    assert hf_leaderboard._map_column_to_benchmark("mmlu_acc") == "mmlu"
    assert hf_leaderboard._map_column_to_benchmark("HellaSwag (norm)") == "hellaswag"
    assert hf_leaderboard._map_column_to_benchmark("ARC-Challenge") == "arc"
    assert hf_leaderboard._map_column_to_benchmark("GSM-8K") == "gsm8k"
    assert hf_leaderboard._map_column_to_benchmark("TruthfulQA mc2") == "truthfulqa"
    assert hf_leaderboard._map_column_to_benchmark("Winogrande") == "winogrande"


def test_hf_map_column_unknown_returns_none():
    assert hf_leaderboard._map_column_to_benchmark("random_column") is None
    assert hf_leaderboard._map_column_to_benchmark("model_name") is None


def test_hf_extract_model_name_picks_first_string_field():
    assert hf_leaderboard._extract_model_name({"model": "foo"}) == "foo"
    assert hf_leaderboard._extract_model_name({"Model": "Bar"}) == "Bar"
    assert hf_leaderboard._extract_model_name({"fullname": "org/baz"}) == "org/baz"
    assert hf_leaderboard._extract_model_name({"unrelated": 5}) is None
    assert hf_leaderboard._extract_model_name({"model": "  "}) is None


# ---------- lmsys_arena helpers ----------


def test_lmsys_pick_column_finds_substring_match():
    headers = ["Model", "Arena Elo", "# Votes"]
    assert lmsys_arena._pick_column(headers, ["Model"]) == 0
    assert lmsys_arena._pick_column(headers, ["Arena Elo"]) == 1
    assert lmsys_arena._pick_column(headers, ["votes"]) == 2


def test_lmsys_pick_column_falls_back_through_candidates():
    headers = ["key", "rating", "battles"]
    assert lmsys_arena._pick_column(headers, ["Model", "key", "name"]) == 0
    assert lmsys_arena._pick_column(headers, ["Arena Elo", "rating"]) == 1
    assert lmsys_arena._pick_column(headers, ["Votes", "battles"]) == 2


def test_lmsys_pick_column_returns_none_when_missing():
    headers = ["something", "else"]
    assert lmsys_arena._pick_column(headers, ["model", "key", "name"]) is None


def test_lmsys_coerce_int_handles_commas_and_strings():
    assert lmsys_arena._coerce_int("1,234") == 1234
    assert lmsys_arena._coerce_int("50000") == 50000
    assert lmsys_arena._coerce_int(50000) == 50000
    assert lmsys_arena._coerce_int(None) is None
    assert lmsys_arena._coerce_int("abc") is None


def test_lmsys_coerce_float_handles_commas_and_strings():
    assert lmsys_arena._coerce_float("1,287.5") == 1287.5
    assert lmsys_arena._coerce_float("1287") == 1287.0
    assert lmsys_arena._coerce_float(None) is None
    assert lmsys_arena._coerce_float("not a number") is None
