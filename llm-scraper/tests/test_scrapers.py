"""
Pure-function tests for scraper helpers. No network. The high-level
`run_scraper()` entry points are exercised indirectly via test_run.py with
monkeypatched stand-ins.
"""

from __future__ import annotations

import pytest

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
    # v2 benchmark set — column headers vary across dataset versions, match
    # loosely via the _normalise_col pathway.
    assert hf_leaderboard._map_column_to_benchmark("IFEval") == "ifeval"
    assert hf_leaderboard._map_column_to_benchmark("leaderboard_ifeval") == "ifeval"
    assert hf_leaderboard._map_column_to_benchmark("BBH") == "bbh"
    assert hf_leaderboard._map_column_to_benchmark("big_bench_hard") == "bbh"
    assert hf_leaderboard._map_column_to_benchmark("MATH Lvl 5 (5-shot)") == "math_lvl5"
    assert hf_leaderboard._map_column_to_benchmark("math_lvl_5") == "math_lvl5"
    assert hf_leaderboard._map_column_to_benchmark("GPQA (0-shot)") == "gpqa"
    assert hf_leaderboard._map_column_to_benchmark("MuSR") == "musr"
    assert hf_leaderboard._map_column_to_benchmark("MMLU-PRO") == "mmlu_pro"
    assert hf_leaderboard._map_column_to_benchmark("mmlu_pro") == "mmlu_pro"


def test_hf_map_column_unknown_returns_none():
    assert hf_leaderboard._map_column_to_benchmark("random_column") is None
    assert hf_leaderboard._map_column_to_benchmark("model_name") is None
    # Plain "MMLU" (v1) should NOT match v2 "MMLU-PRO" — different benchmark.
    # Our token list only has "mmlupro", so plain "mmlu" doesn't resolve.
    assert hf_leaderboard._map_column_to_benchmark("mmlu") is None


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


# ---------- LMSYS pickle walker (v2 code path) ----------


def test_lmsys_walk_pickle_extracts_elo_dataframe():
    """Given a dict-nested pandas DataFrame shaped like elo_results_*.pkl,
    _walk_pickle_for_elo should find it and produce Arena Elo records."""
    pd = pytest.importorskip("pandas")

    df = pd.DataFrame(
        {
            "model": ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro"],
            "rating": [1287.3, 1271.1, 1260.4],
            "num_battles": [50000, 48000, 30000],
        }
    )
    # Mimic the nested structure lmsys/chatbot-arena-leaderboard actually
    # publishes: {"full": {"leaderboard_table_df": <DataFrame>}, ...}
    payload = {"full": {"leaderboard_table_df": df, "unrelated": None}}

    records = lmsys_arena._walk_pickle_for_elo(payload)

    assert len(records) == 3
    by_model = {r["model_raw_name"]: r for r in records}
    assert by_model["gpt-4o"]["score"] == 1287.3
    assert by_model["gpt-4o"]["benchmark"] == "lmsys_elo"
    assert by_model["gpt-4o"]["votes"] == 50000
    assert by_model["claude-3-5-sonnet"]["votes"] == 48000


def test_lmsys_walk_pickle_returns_empty_when_no_rating_column():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"model": ["foo"], "some_other_metric": [42]})
    records = lmsys_arena._walk_pickle_for_elo({"full": df})
    assert records == []


def test_lmsys_walk_pickle_uses_index_when_model_column_absent():
    """If the DataFrame is indexed by model name (common pattern), we should
    fall back to the index for the model identifier."""
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame(
        {"rating": [1287.3, 1271.1]},
        index=["gpt-4o", "claude-3-5-sonnet"],
    )
    records = lmsys_arena._walk_pickle_for_elo({"full": df})
    models = {r["model_raw_name"] for r in records}
    assert models == {"gpt-4o", "claude-3-5-sonnet"}


# ---------- LMSYS JSON API response parser ----------


def test_lmsys_records_from_json_list_of_dicts():
    payload = [
        {"model": "gpt-4o", "rating": 1287, "votes": 50000},
        {"model": "claude-3-5-sonnet", "rating": 1271, "votes": 48000},
    ]
    records = lmsys_arena._records_from_json_payload(payload)
    assert {r["model_raw_name"] for r in records} == {"gpt-4o", "claude-3-5-sonnet"}
    assert all(r["benchmark"] == "lmsys_elo" for r in records)


def test_lmsys_records_from_json_dict_wrapper():
    payload = {
        "leaderboard": [
            {"name": "gpt-4o", "arena_elo": 1287.0, "num_battles": 50000},
        ]
    }
    records = lmsys_arena._records_from_json_payload(payload)
    assert records[0]["model_raw_name"] == "gpt-4o"
    assert records[0]["score"] == 1287.0
    assert records[0]["votes"] == 50000


def test_lmsys_records_from_json_skips_rows_without_rating():
    payload = [{"model": "foo"}, {"model": "bar", "rating": "not-a-number"}]
    records = lmsys_arena._records_from_json_payload(payload)
    assert records == []


# ---------- LMSYS MT-bench CSV fallback (4th-tier source) ----------


def test_lmsys_mtbench_csv_parses_known_columns(monkeypatch):
    """End-to-end check of the MT-bench fallback: simulate the Space tree
    advertising a dated CSV with the real-world column header we saw in CI,
    then verify the scraper emits benchmark='mtbench' records."""

    # Simulated Space tree: two dated CSVs plus unrelated files.
    fake_tree = [
        {"type": "file", "path": "README.md"},
        {"type": "file", "path": "leaderboard_table_20250101.csv"},
        {"type": "file", "path": "leaderboard_table_20250804.csv"},
        {"type": "file", "path": "elo_results_20250804.pkl"},
    ]
    # Exact header we observed in the failing CI run plus a couple of rows.
    fake_csv = (
        "key,Model,MT-bench (score),MMLU,Knowledge cutoff date,License,Organization,Link\n"
        "gpt-4o,GPT-4o,9.32,0.887,2024-10,Proprietary,OpenAI,https://openai.com\n"
        "claude-3-5-sonnet,Claude 3.5 Sonnet,8.95,0.883,2024-04,Proprietary,Anthropic,https://anthropic.com\n"
        ",,,,,,,\n"  # junk row: should be skipped
    )

    def fake_get_json(client, url):
        assert url == lmsys_arena.SPACE_TREE_API
        return fake_tree

    def fake_get_text(client, url):
        # Should pick the newer CSV first (2025-08-04 > 2025-01-01).
        assert url.endswith("leaderboard_table_20250804.csv")
        return fake_csv

    monkeypatch.setattr(lmsys_arena, "_http_get_json", fake_get_json)
    monkeypatch.setattr(lmsys_arena, "_http_get_text", fake_get_text)

    records = lmsys_arena._fetch_via_mtbench_csv(client=None)

    assert len(records) == 2
    by_model = {r["model_raw_name"]: r for r in records}
    assert by_model["GPT-4o"]["benchmark"] == "mtbench"
    assert by_model["GPT-4o"]["score"] == 9.32
    assert by_model["Claude 3.5 Sonnet"]["score"] == 8.95


def test_lmsys_mtbench_csv_returns_empty_when_no_mtbench_column(monkeypatch):
    fake_tree = [{"type": "file", "path": "leaderboard_table_20250804.csv"}]
    fake_csv = "key,Model,MMLU,Organization\ngpt-4o,GPT-4o,0.887,OpenAI\n"

    monkeypatch.setattr(lmsys_arena, "_http_get_json", lambda c, u: fake_tree)
    monkeypatch.setattr(lmsys_arena, "_http_get_text", lambda c, u: fake_csv)

    assert lmsys_arena._fetch_via_mtbench_csv(client=None) == []
