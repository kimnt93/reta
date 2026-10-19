import json
import subprocess
import sys
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from reta.contracts import AlphaSpec, RetaError
from reta.data import load_bars
from reta.models import convert, positions_for, replay


def test_sma_absolute_targets_and_unchanged_rows(make_bars):
    bars = make_bars([10.0, 11.0, 12.0, 9.0, 8.0, 10.0, 11.0])
    spec = AlphaSpec(family="sma_regime", lookback=3, units=2)
    generated = positions_for(bars, spec)
    assert generated["target_units"].to_list() == [2, -2, -2, 2, 2]
    assert generated["decision_ts"].dt.hour().to_list() == [3, 4, 5, 6, 7]
    assert (
        generated["effective_ts"].to_list()
        == generated["decision_ts"].to_list()
    )


@pytest.mark.parametrize(
    "family", ["sma_regime", "channel_breakout", "zscore_reversion"]
)
def test_future_append_does_not_change_existing_decisions(make_bars, family):
    values = [10.0, 11.0, 12.0, 9.0, 8.0, 10.0, 11.0]
    spec = AlphaSpec(family=family, lookback=3)
    original = positions_for(make_bars(values), spec)
    extended = positions_for(make_bars([*values, 900.0]), spec)
    assert_frame_equal(original, extended.slice(0, original.height))


def test_delayed_decision_waits_for_scheduled_open(make_bars):
    bars = make_bars([10.0, 11.0, 12.0, 9.0, 8.0])
    bars = bars.with_columns(
        (pl.col("available_ts") + pl.duration(minutes=30)).alias(
            "available_ts"
        ),
        pl.when(pl.col("open_ts") == pl.col("open_ts").max())
        .then(pl.col("next_open_ts") + pl.duration(hours=1))
        .otherwise(pl.col("next_open_ts"))
        .alias("next_open_ts"),
    )
    generated = positions_for(bars, AlphaSpec(family="sma_regime", lookback=3))
    assert generated["effective_ts"].dt.hour().to_list() == [4, 6, 6]
    assert generated["decision_ts"].dt.minute().to_list() == [30, 30, 30]


def test_equality_is_explicit_flat_and_groups_do_not_mix(make_bars):
    first = make_bars([10.0, 10.0, 10.0], "A")
    second = make_bars([100.0, 110.0, 120.0], "B")
    generated = positions_for(
        pl.concat([first, second]),
        AlphaSpec(family="sma_regime", lookback=3),
    )
    assert generated["target_units"].to_list() == [0, 1]


def test_expected_bar_gap_is_not_skipped(make_bars, tmp_path):
    bars = make_bars([10.0, 11.0, 12.0, 9.0])
    path = tmp_path / "bars.parquet"
    bars.filter(pl.col("open_ts").dt.hour() != 1).write_parquet(path)
    with pytest.raises(RetaError, match="scheduled bar"):
        load_bars(path)


def test_standalone_export_matches_runtime_and_tamper_is_rejected(
    make_bars, tmp_path
):
    bars_path = tmp_path / "bars.parquet"
    make_bars([10.0, 11.0, 12.0, 9.0]).write_parquet(bars_path)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        AlphaSpec(family="sma_regime", lookback=3).model_dump_json()
    )
    result = convert(spec_path, bars_path, tmp_path / "output")
    bundle = Path(result["bundle"])
    output = tmp_path / "standalone.parquet"
    subprocess.run(
        [
            sys.executable,
            str(bundle / "model.py"),
            "--bars",
            str(bars_path),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    assert_frame_equal(
        pl.read_parquet(output),
        pl.read_parquet(bundle / "positions.parquet"),
    )
    changed = json.loads((bundle / "spec.json").read_text())
    changed["units"] = 900
    (bundle / "spec.json").write_text(json.dumps(changed))
    with pytest.raises(RetaError, match="Changed artifact"):
        replay(bundle, bars_path, tmp_path / "should-not-exist.parquet")


def test_unknown_finality_is_not_a_final_bar(make_bars, tmp_path):
    path = tmp_path / "bars.parquet"
    make_bars([10.0, 11.0, 12.0]).with_columns(
        pl.Series("is_final", [True, None, True]),
    ).write_parquet(path)
    with pytest.raises(RetaError, match="Only final bars"):
        load_bars(path)
