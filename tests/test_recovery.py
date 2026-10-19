import json
from pathlib import Path

import polars as pl
import pytest

from reta.contracts import AlphaSpec, EvaluationPolicy
from reta.demo import create_demo
from reta.evaluation import assess, measure, transition_metrics
from reta.research import reverse


def test_unknown_half_of_history_cannot_pass_perfect_known_labels():
    directions = [0, 1] * 50 + [None] * 100
    frame = pl.DataFrame(
        {
            "direction": directions,
            "quantity_units": directions,
            "target_units": [0, 1] * 50 + [0] * 100,
        }
    )
    metrics = measure(frame, tolerance=0)
    assert metrics["macro_f1"] == 1
    outcome, failures = assess(
        metrics,
        EvaluationPolicy(minimum_coverage=0.9),
        claim="absolute_positions",
        baseline=0,
    )
    assert outcome == "insufficient_evidence"
    assert failures == ["minimum_coverage"]


def test_one_prediction_cannot_match_two_observed_transitions():
    frame = pl.DataFrame(
        {
            "direction": [0, 1, 0, 1, 0],
            "target_units": [0, 0, 0, 1, 0],
        }
    )
    result = transition_metrics(frame, tolerance=3)
    assert result["matched_transitions"] == 2
    assert result["observed_transitions"] == 4
    assert result["transition_f1"] == pytest.approx(2 / 3)


def test_failed_behavior_emits_no_model_instead_of_weakening_gates(tmp_path):
    request_path = create_demo(tmp_path / "source")
    request = json.loads(request_path.read_text())
    request["families"] = []
    request["candidate_specs"] = [
        AlphaSpec(
            family="sma_regime",
            lookback=3,
            band_bps=1_000_000,
            units=2,
        ).model_dump()
    ]
    request["max_trials"] = 1
    request_path.write_text(json.dumps(request))
    result = reverse(request_path, tmp_path / "output")
    assert result["outcome"] == "no_candidate_passed"
    assert "minimum_macro_f1" in result["failed_gates"]
    assert result["backtest"]["status"] == "completed"
    assert [scope["scope"] for scope in result["backtest"]["scopes"]] == [
        "full",
        "held_out",
    ]
    assert not (Path(result["bundle"]) / "model.py").exists()
    trials = json.loads((Path(result["bundle"]) / "trials.json").read_text())
    assert trials[0]["validation"]["macro_f1"] == 0


def test_bundle_request_repeats_without_original_source(tmp_path):
    request_path = create_demo(tmp_path / "source")
    request = json.loads(request_path.read_text())
    request["families"] = []
    request["candidate_specs"] = [
        AlphaSpec(
            family="sma_regime",
            lookback=5,
            units=2,
        ).model_dump()
    ]
    request_path.write_text(json.dumps(request))
    first = reverse(request_path, tmp_path / "output")
    assert first["outcome"] == "succeeded"
    request_path.parent.rename(tmp_path / "unavailable-source")
    second = reverse(
        Path(first["bundle"]) / "request.json", tmp_path / "rerun"
    )
    assert second["outcome"] == "succeeded"
    first_spec = json.loads((Path(first["bundle"]) / "spec.json").read_text())
    second_spec = json.loads(
        (Path(second["bundle"]) / "spec.json").read_text()
    )
    assert first_spec == second_spec
