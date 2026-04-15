"""
Behavioral tests for diff.compute_diff().
"""

from __future__ import annotations

from typing import Any

from diff import compute_diff


def _master(models: dict[str, Any]) -> dict[str, Any]:
    return {"generated_at": "2025-01-19T00:00:00Z", "schema_version": "1", "models": models}


def _model(display: str, provider: str, scores: dict[str, Any]) -> dict[str, Any]:
    return {"display_name": display, "provider": provider, "scores": scores}


def _score(value: float, source: str = "hf_leaderboard", btype: str | None = "knowledge") -> dict[str, Any]:
    s = {"score": value, "source": source, "recorded_at": "2025-01-19T00:00:00Z"}
    if btype:
        s["benchmark_type"] = btype
    return s


def test_no_archive_writes_empty_stub(scenario):
    payload = compute_diff()
    assert payload["from_snapshot"] is None
    assert payload["summary"] == {"models_added": 0, "models_updated": 0, "scores_changed": 0}
    assert payload["added"] == []
    assert payload["updated"] == []
    assert payload["removed"] == []


def test_added_model_appears_in_added_list(scenario):
    scenario.write_archive("2025-01-12", _master({}))
    scenario.write_master(
        _master(
            {
                "gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(88.7)}),
            }
        )
    )

    payload = compute_diff()
    assert payload["summary"]["models_added"] == 1
    assert payload["from_snapshot"] == "master_2025-01-12.json"
    assert payload["added"][0]["canonical_id"] == "gpt-4o"
    assert payload["added"][0]["display_name"] == "GPT-4o"
    assert payload["added"][0]["provider"] == "OpenAI"


def test_score_change_records_delta_and_benchmark_type(scenario):
    scenario.write_archive(
        "2025-01-12",
        _master(
            {
                "gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(88.0, btype="knowledge")}),
            }
        ),
    )
    scenario.write_master(
        _master(
            {
                "gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(89.5, btype="knowledge")}),
            }
        )
    )

    payload = compute_diff()
    assert payload["summary"]["models_updated"] == 1
    assert payload["summary"]["scores_changed"] == 1

    upd = payload["updated"][0]
    assert upd["canonical_id"] == "gpt-4o"
    assert upd["display_name"] == "GPT-4o"
    change = upd["changes"][0]
    assert change["benchmark"] == "mmlu"
    assert change["benchmark_type"] == "knowledge"
    assert change["old_score"] == 88.0
    assert change["new_score"] == 89.5
    assert change["delta"] == 1.5


def test_removed_model_in_removed_list(scenario):
    scenario.write_archive(
        "2025-01-12",
        _master(
            {
                "gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(88.0)}),
                "old-model": _model("Old Model", "Defunct", {"mmlu": _score(50.0)}),
            }
        ),
    )
    scenario.write_master(
        _master(
            {
                "gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(88.0)}),
            }
        )
    )

    payload = compute_diff()
    assert payload["summary"]["models_added"] == 0
    assert payload["summary"]["models_updated"] == 0
    assert len(payload["removed"]) == 1
    assert payload["removed"][0]["canonical_id"] == "old-model"
    assert payload["removed"][0]["provider"] == "Defunct"


def test_unchanged_model_not_in_updated(scenario):
    same = _master(
        {
            "gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(88.7)}),
        }
    )
    scenario.write_archive("2025-01-12", same)
    scenario.write_master(same)

    payload = compute_diff()
    assert payload["summary"]["models_updated"] == 0
    assert payload["updated"] == []


def test_diff_picks_latest_archive_when_multiple_exist(scenario):
    """Older archive should be ignored — only the most recent one is the
    baseline."""
    scenario.write_archive(
        "2025-01-05",
        _master({"gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(70.0)})}),
    )
    scenario.write_archive(
        "2025-01-12",
        _master({"gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(88.0)})}),
    )
    scenario.write_master(
        _master({"gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(89.5)})})
    )

    payload = compute_diff()
    assert payload["from_snapshot"] == "master_2025-01-12.json"
    change = payload["updated"][0]["changes"][0]
    assert change["old_score"] == 88.0  # NOT 70.0
    assert change["new_score"] == 89.5


def test_new_benchmark_on_existing_model_counted_as_score_change(scenario):
    scenario.write_archive(
        "2025-01-12",
        _master(
            {
                "gpt-4o": _model("GPT-4o", "OpenAI", {"mmlu": _score(88.0)}),
            }
        ),
    )
    scenario.write_master(
        _master(
            {
                "gpt-4o": _model(
                    "GPT-4o",
                    "OpenAI",
                    {
                        "mmlu": _score(88.0),
                        "lmsys_elo": _score(1287.0, source="lmsys_arena", btype="human_preference"),
                    },
                ),
            }
        )
    )

    payload = compute_diff()
    assert payload["summary"]["scores_changed"] == 1
    change = payload["updated"][0]["changes"][0]
    assert change["benchmark"] == "lmsys_elo"
    assert change["benchmark_type"] == "human_preference"
    assert change["old_score"] is None
    assert change["new_score"] == 1287.0
