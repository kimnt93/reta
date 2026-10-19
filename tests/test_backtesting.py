import json
from pathlib import Path

import polars as pl
import pytest

from reta.backtesting import run_backtest
from reta.contracts import AlphaSpec, BacktestConfig, RetaError
from reta.models import backtest_bundle, convert


def targets(bars, indices, units):
    schedule = pl.concat([bars["open_ts"], bars["next_open_ts"].tail(1)])
    selected = schedule.gather(indices)
    return pl.DataFrame(
        {
            "instrument_id": [bars["instrument_id"][0]] * len(indices),
            "decision_ts": selected,
            "effective_ts": selected,
            "target_units": units,
        }
    )


def no_costs(**changes):
    return BacktestConfig(
        initial_cash=1000,
        fees_bps=0,
        slippage_bps=0,
        **changes,
    )


def test_net_reversal_fees_slippage_and_initial_peak_drawdown(make_bars):
    bars = make_bars([100.0, 110.0, 90.0, 95.0]).with_columns(
        pl.Series("open", [100.0, 105.0, 100.0, 90.0]),
    )
    result = run_backtest(
        bars,
        targets(bars, [0, 1, 2], [1, -1, 0]),
        BacktestConfig(
            initial_cash=1000, fees_bps=100, fixed_fee=1, slippage_bps=10
        ),
    )
    metrics = result.summary["instruments"][0]
    assert result.orders["size"].to_list() == [1, 2, 1]
    assert result.orders["price"].to_list() == pytest.approx(
        [100.1, 104.895, 100.1]
    )
    assert metrics["total_fees"] == pytest.approx(7.0999)
    assert metrics["net_pnl"] == pytest.approx(2.4901)
    assert metrics["final_equity"] == pytest.approx(1002.4901)
    assert metrics["max_drawdown_pct"] == pytest.approx(0.54089)
    assert metrics["closed_trades"] == 2
    assert metrics["open_trades"] == 0
    assert metrics["profit_factor"] is None


def test_effective_open_fill_and_pending_target_do_not_force_final_close(
    make_bars,
):
    bars = make_bars([100.0, 110.0, 90.0])
    result = run_backtest(bars, targets(bars, [1, 3], [1, 0]), no_costs())
    metrics = result.summary["instruments"][0]
    assert result.orders["price"].to_list() == [100]
    assert result.orders["execution_ts"].to_list() == [bars["open_ts"][1]]
    assert metrics["pending_targets"] == 1
    assert metrics["filled_orders"] == 1
    assert metrics["closed_trades"] == 0
    assert metrics["open_trades"] == 1
    assert metrics["net_pnl"] == pytest.approx(-10)
    assert result.trades["exit_ts"].to_list() == [None]
    assert result.trades["exit_price"].to_list() == [None]
    assert result.trades["mark_price"].to_list() == [90]


def test_latest_decision_at_shared_open_wins_without_extra_fills(make_bars):
    bars = make_bars([100.0, 110.0, 90.0, 95.0])
    positions = (
        targets(bars, [3, 3], [1, -2])
        .with_columns(
            pl.Series("delay_minutes", [20, 10]),
        )
        .with_columns(
            (
                pl.col("decision_ts")
                - pl.duration(minutes=pl.col("delay_minutes"))
            )
            .cast(pl.Datetime("ns", "UTC"))
            .alias("decision_ts"),
        )
        .drop("delay_minutes")
    )
    result = run_backtest(bars, positions, no_costs())
    assert result.orders["side"].to_list() == ["sell"]
    assert result.orders["size"].to_list() == [2]
    assert result.equity["quantity_units"][-1] == -2
    assert result.summary["instruments"][0]["net_pnl"] == pytest.approx(-10)


@pytest.mark.parametrize("quantity", [2, -2])
@pytest.mark.parametrize("initial_cash", [50, 150])
def test_insufficient_cash_rejects_instead_of_resizing(
    make_bars,
    quantity,
    initial_cash,
):
    bars = make_bars([100.0, 100.0])
    result = run_backtest(
        bars,
        targets(bars, [0, 1], [quantity, quantity]),
        BacktestConfig(initial_cash=initial_cash, fees_bps=0, slippage_bps=0),
    )
    metrics = result.summary["instruments"][0]
    assert metrics["unfilled_orders"] == 2
    assert metrics["rejected_orders"] + metrics["ignored_unfilled_orders"] == 2
    assert metrics["filled_orders"] == 0
    assert metrics["final_equity"] == initial_cash
    assert result.equity["quantity_units"].to_list() == [0, 0]
    assert result.rejections["target_units"].to_list() == [quantity, quantity]


def test_held_out_starts_flat_and_excludes_pending_training_decisions(
    make_bars,
):
    bars = make_bars([100.0, 110.0, 120.0, 130.0, 140.0])
    positions = targets(bars, [0, 2, 4], [1, 2, -1]).with_columns(
        pl.when(pl.col("effective_ts") == bars["open_ts"][2])
        .then(pl.col("effective_ts") - pl.duration(minutes=30))
        .otherwise(pl.col("decision_ts"))
        .cast(pl.Datetime("ns", "UTC"))
        .alias("decision_ts"),
    )
    start = bars["open_ts"].cast(pl.Int64)[2]
    result = run_backtest(
        bars,
        positions,
        no_costs(),
        scope="held_out",
        start_ns=start,
    )
    assert result.equity["quantity_units"].to_list() == [0, 0, -1]
    assert result.equity["equity"].to_list() == [1000, 1000, 990]
    assert result.orders["execution_ts"].to_list() == [bars["open_ts"][4]]


def test_instruments_get_independent_capital(make_bars):
    first = make_bars([100.0, 110.0], "A")
    second = make_bars([50.0, 40.0], "B")
    result = run_backtest(
        pl.concat([first, second]),
        pl.concat([targets(first, [0], [1]), targets(second, [0], [1])]),
        no_costs(),
    )
    metrics = {
        item["instrument_id"]: item for item in result.summary["instruments"]
    }
    assert metrics["A"]["initial_cash"] == 1000
    assert metrics["B"]["initial_cash"] == 1000
    assert metrics["A"]["final_equity"] == 1010
    assert metrics["B"]["final_equity"] == 990


def test_missing_open_does_not_move_fill_to_another_bar(make_bars):
    bars = make_bars([100.0, 110.0, 90.0])
    positions = targets(bars, [0], [1]).with_columns(
        (pl.col("effective_ts") + pl.duration(minutes=30))
        .cast(pl.Datetime("ns", "UTC"))
        .alias("effective_ts"),
    )
    with pytest.raises(RetaError) as error:
        run_backtest(bars, positions, no_costs())
    assert error.value.code == "invalid_backtest_target"


def test_conversion_and_rebacktest_preserve_costs_and_actual_results(
    make_bars, tmp_path
):
    bars_path = tmp_path / "bars.parquet"
    make_bars([10.0, 11.0, 12.0, 9.0]).write_parquet(bars_path)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        AlphaSpec(
            family="sma_regime",
            lookback=3,
            units=2,
        ).model_dump_json()
    )
    converted = convert(
        spec_path, bars_path, tmp_path / "output", backtest=no_costs()
    )
    original = json.loads(
        (Path(converted["bundle"]) / "backtest.json").read_text()
    )
    metrics = original["scopes"][0]["instruments"][0]
    assert metrics["net_pnl"] == pytest.approx(-6)
    assert metrics["pending_targets"] == 1
    assert metrics["closed_trades"] == 0
    rerun = backtest_bundle(Path(converted["bundle"]), tmp_path / "output")
    assert rerun["backtest"]["config"] == original["config"]
    assert rerun["backtest"]["scopes"][0]["instruments"][0][
        "net_pnl"
    ] == pytest.approx(-6)


def test_flat_and_unchanged_targets_do_not_create_extra_fees(make_bars):
    bars = make_bars([100.0, 101.0, 101.0, 100.0])
    result = run_backtest(
        bars,
        targets(bars, [0, 1, 2, 3], [0, 1, 1, 0]),
        no_costs(fixed_fee=1),
    )
    metrics = result.summary["instruments"][0]
    assert metrics["filled_orders"] == 2
    assert metrics["total_fees"] == 2
    assert metrics["unfilled_orders"] == 0
    assert metrics["net_pnl"] == pytest.approx(-1)


@pytest.mark.parametrize(
    ("closes", "periods", "expected"),
    [
        ([100.0, 110.0, 105.0], None, None),
        ([100.0, 110.0, 105.0], 252, 3.5083136010249603),
        ([100.0, 100.0, 100.0], 252, None),
    ],
)
def test_sharpe_requires_explicit_periods_and_nonzero_variance(
    make_bars,
    closes,
    periods,
    expected,
):
    bars = make_bars(closes)
    result = run_backtest(
        bars,
        targets(bars, [0], [1]),
        no_costs(periods_per_year=periods),
    )
    metric = result.summary["instruments"][0]
    if expected is None:
        assert metric["sharpe_ratio"] is None
    else:
        # Equity 1000 -> 1010 -> 1005; sample-std, 252 periods/year.
        assert metric["sharpe_ratio"] == pytest.approx(expected)
