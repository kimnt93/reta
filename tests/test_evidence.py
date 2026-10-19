from pathlib import Path

import polars as pl
import pytest

from reta.contracts import (
    AlphaSpec,
    EvaluationPolicy,
    ResearchRequest,
    RetaError,
)
from reta.data import align_labels, labels_for
from reta.evaluation import assess, measure
from reta.models import positions_for
from reta.research import fit, reverse, split_boundaries


def request(**changes):
    fields = {
        "objective": "Reconstruct fixture",
        "bars": "bars.parquet",
        "observations": "observations.parquet",
        "source_type": "paper",
        "permission": "Owned fixture",
        **changes,
    }
    return ResearchRequest.model_validate(fields)


def test_partial_close_reversal_and_event_identity(make_bars):
    times = make_bars([10.0, 11.0, 12.0])["close_ts"]
    events = pl.DataFrame(
        {
            "instrument_id": ["X"] * 4,
            "event_id": ["a", "b", "c", "c"],
            "event_ts": [times[0], times[1], times[2], times[2]],
            "side": ["buy", "sell", "sell", "sell"],
            "quantity": [10, 4, 8, 8],
        }
    )
    labels = labels_for(
        request(
            observation_kind="executions",
            initial_position=0,
            complete_history=True,
        ),
        events,
    )
    assert labels["quantity_units"].to_list() == [10, 6, -2]
    conflicting = events.with_columns(
        pl.Series("quantity", [10, 4, 8, 9]),
    )
    with pytest.raises(RetaError, match="conflicting records"):
        labels_for(
            request(
                observation_kind="executions",
                initial_position=0,
                complete_history=True,
            ),
            conflicting,
        )


def test_unknown_interval_is_not_flat_or_carried_through(make_bars):
    bars = make_bars([10.0, 11.0, 12.0, 9.0, 8.0, 10.0])
    times = bars["close_ts"]
    observations = pl.DataFrame(
        {
            "instrument_id": ["X"] * 3,
            "event_ts": [times[2], times[3], times[5]],
            "target_units": [2, None, -2],
        }
    )
    labels = labels_for(request(complete_history=True), observations)
    positions = positions_for(bars, AlphaSpec(family="sma_regime", lookback=3))
    aligned = align_labels(positions, labels, continuous=True)
    assert aligned["quantity_units"].to_list() == [2, None, None, -2]


def test_sparse_or_constant_labels_cannot_pass_by_accuracy():
    frame = pl.DataFrame(
        {
            "direction": [0] * 100,
            "target_units": [0] * 100,
            "quantity_units": [0] * 100,
        }
    )
    metrics = measure(frame, tolerance=1)
    outcome, gates = assess(
        metrics,
        EvaluationPolicy(),
        claim="absolute_positions",
        baseline=1,
    )
    assert outcome == "insufficient_evidence"
    assert "minimum_transitions" in gates
    assert "minimum_classes" in gates


def test_fractional_direction_is_not_silently_truncated(make_bars):
    observations = pl.DataFrame(
        {
            "instrument_id": ["X"],
            "event_ts": [make_bars([10.0])["close_ts"][0]],
            "direction": [1.5],
        }
    )
    with pytest.raises(RetaError, match="Expected -1"):
        labels_for(request(), observations)


def test_test_labels_cannot_change_fit_or_validation_selection(make_bars):
    values = [100.0 + (index % 9) for index in range(400)]
    bars = make_bars(values)
    spec = AlphaSpec(family="sma_regime", lookback=3)
    generated = positions_for(bars, spec)
    observations = generated.select(
        "instrument_id",
        pl.col("effective_ts").alias("event_ts"),
        "target_units",
    )
    configured = request(
        max_lookback=10, families=["sma_regime"], max_trials=6
    )
    boundaries = split_boundaries(bars, configured)
    original = labels_for(configured, observations)
    mutated = original.with_columns(
        pl.when(
            pl.col("event_ts").cast(pl.Int64)
            >= boundaries["validation_end_ns"]
        )
        .then(-pl.col("direction"))
        .otherwise(pl.col("direction"))
        .alias("direction"),
        pl.when(
            pl.col("event_ts").cast(pl.Int64)
            >= boundaries["validation_end_ns"]
        )
        .then(-pl.col("quantity_units"))
        .otherwise(pl.col("quantity_units"))
        .alias("quantity_units"),
    )
    before, trials_before = fit(bars, original, configured, boundaries)
    after, trials_after = fit(bars, mutated, configured, boundaries)
    assert before == after
    assert trials_before == trials_after


def test_pnl_only_publishes_no_model_report(make_bars, tmp_path):
    make_bars([10.0, 11.0, 12.0]).write_parquet(tmp_path / "bars.parquet")
    pl.DataFrame({"pnl": [1, 2, 3]}).write_parquet(
        tmp_path / "observations.parquet"
    )
    configured = request(observation_kind="pnl")
    path = tmp_path / "request.json"
    path.write_text(configured.model_dump_json())
    result = reverse(path, tmp_path / "output")
    assert result["outcome"] == "insufficient_evidence"
    bundle = Path(result["bundle"])
    assert result["backtest"]["status"] == "not_run"
    assert "scopes" not in result["backtest"]
    assert not (bundle / "backtest_equity.parquet").exists()
    assert not (bundle / "model.py").exists()
