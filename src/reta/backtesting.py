"""Causal target-position simulation using the actual vectorbt engine."""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from reta.artifacts import write_json
from reta.contracts import BacktestConfig, RetaError


@dataclass(frozen=True, slots=True)
class BacktestRun:
    summary: dict[str, Any]
    equity: pl.DataFrame
    orders: pl.DataFrame
    trades: pl.DataFrame
    rejections: pl.DataFrame


def _stamp(series: pl.Series, offset: int) -> str:
    return series.slice(offset, 1).dt.to_string("%+").item()


def _finite(value: float) -> float | None:
    number = float(value)
    return number if math.isfinite(number) else None


def _timeline(
    bars: pl.DataFrame,
    positions: pl.DataFrame,
) -> tuple[pl.DataFrame, int]:
    chosen = positions.sort(["effective_ts", "decision_ts"]).unique(
        subset=["effective_ts"],
        keep="last",
        maintain_order=True,
    )
    if chosen.filter(pl.col("decision_ts") > pl.col("effective_ts")).height:
        raise RetaError(
            "invalid_backtest_target", "Target precedes its decision"
        )
    last_open = bars["open_ts"].max()
    pending = chosen.filter(pl.col("effective_ts") > last_open).height
    executable = chosen.filter(pl.col("effective_ts") <= last_open)
    unknown = executable.join(
        bars.select(pl.col("open_ts").alias("effective_ts")),
        on="effective_ts",
        how="anti",
    )
    if unknown.height:
        raise RetaError(
            "invalid_backtest_target", "Target is not a recorded opening"
        )
    timeline = bars.join(
        executable.select("effective_ts", "target_units"),
        left_on="open_ts",
        right_on="effective_ts",
        how="left",
    ).sort("open_ts")
    return timeline, pending


def _simulate(timeline: pl.DataFrame, config: BacktestConfig):
    import vectorbt as vbt

    target = timeline["target_units"].cast(pl.Float64).to_numpy()
    return vbt.Portfolio.from_orders(
        timeline["close"].to_numpy(),
        size=target,
        price=timeline["open"].to_numpy(),
        size_type="targetamount",
        direction="both",
        init_cash=config.initial_cash,
        fees=config.fees_bps / 10_000,
        fixed_fees=config.fixed_fee,
        slippage=config.slippage_bps / 10_000,
        size_granularity=1,
        lock_cash=True,
        allow_partial=False,
        raise_reject=False,
        reject_prob=0,
        log=~np.isnan(target),
        cash_sharing=False,
        trades_type="exittrades",
    )


def _equity(
    portfolio, timeline: pl.DataFrame, initial_cash: float
) -> pl.DataFrame:
    frame = timeline.select(
        "open_ts", "close_ts", "target_units"
    ).with_columns(
        pl.Series("equity", np.asarray(portfolio.value())),
        pl.Series("cash", np.asarray(portfolio.cash())),
        pl.Series("quantity_units", np.asarray(portfolio.assets())),
        pl.Series("return", np.asarray(portfolio.returns())),
    )
    return frame.with_columns(
        (
            1
            - pl.col("equity")
            / pl.col("equity")
            .cum_max()
            .clip(
                lower_bound=initial_cash,
            )
        ).alias("drawdown"),
    ).rename({"close_ts": "valuation_ts"})


def _orders(portfolio, timeline: pl.DataFrame) -> pl.DataFrame:
    times = timeline.with_row_index("idx").select("idx", "open_ts")
    return (
        pl.DataFrame(portfolio.orders.records_arr)
        .join(
            times,
            on="idx",
            how="left",
        )
        .rename({"id": "order_id", "open_ts": "execution_ts"})
        .with_columns(
            pl.when(pl.col("side") == 0)
            .then(pl.lit("buy"))
            .otherwise(pl.lit("sell"))
            .alias("side"),
        )
        .drop("col", "idx")
    )


def _trades(portfolio, timeline: pl.DataFrame) -> pl.DataFrame:
    times = timeline.with_row_index("idx")
    entry_times = times.select(
        pl.col("idx").alias("entry_idx"),
        pl.col("open_ts").alias("entry_ts"),
    )
    exit_times = times.select(
        pl.col("idx").alias("exit_idx"),
        pl.col("open_ts").alias("exit_open_ts"),
        "close_ts",
    )
    frame = (
        pl.DataFrame(portfolio.trades.records_arr)
        .join(
            entry_times,
            on="entry_idx",
            how="left",
        )
        .join(exit_times, on="exit_idx", how="left")
    )
    return (
        frame.with_columns(
            pl.when(pl.col("status") == 1)
            .then(pl.col("exit_open_ts"))
            .otherwise(None)
            .alias("exit_ts"),
            pl.when(pl.col("status") == 0)
            .then(pl.col("close_ts"))
            .otherwise(pl.col("exit_open_ts"))
            .alias("valuation_ts"),
            pl.when(pl.col("status") == 0)
            .then(pl.col("exit_price"))
            .otherwise(None)
            .alias("mark_price"),
            pl.when(pl.col("status") == 1)
            .then(pl.col("exit_price"))
            .otherwise(None)
            .alias("exit_price"),
            pl.when(pl.col("direction") == 0)
            .then(pl.lit("long"))
            .otherwise(pl.lit("short"))
            .alias("direction"),
            pl.when(pl.col("status") == 1)
            .then(pl.lit("closed"))
            .otherwise(pl.lit("open"))
            .alias("status"),
        )
        .rename({"id": "trade_id"})
        .drop(
            "col",
            "entry_idx",
            "exit_idx",
            "exit_open_ts",
            "close_ts",
        )
    )


def _rejections(portfolio, timeline: pl.DataFrame) -> pl.DataFrame:
    from vectorbt.portfolio.enums import OrderStatus, OrderStatusInfo

    rejected = pl.col("res_status") == OrderStatus.Rejected
    ignored = pl.col("res_status") == OrderStatus.Ignored
    unmet = pl.col("req_size") != pl.col("new_position")
    logs = (
        pl.DataFrame(portfolio.logs.records_arr)
        .filter(
            rejected | (ignored & unmet),
        )
        .select(
            "idx",
            pl.col("req_size").alias("target_units"),
            pl.col("req_price").alias("requested_price"),
            pl.col("res_status_info").alias("reason_code"),
            pl.col("res_status").alias("engine_status_code"),
        )
    )
    times = timeline.with_row_index("idx").select("idx", "open_ts")
    names = {value: name for name, value in OrderStatusInfo._asdict().items()}
    return (
        logs.join(times, on="idx", how="left")
        .with_columns(
            pl.col("reason_code")
            .replace_strict(names, default="unknown")
            .alias("reason"),
            pl.col("engine_status_code")
            .replace_strict(
                {
                    OrderStatus.Rejected: "rejected",
                    OrderStatus.Ignored: "ignored",
                }
            )
            .alias("engine_status"),
        )
        .rename({"open_ts": "execution_ts"})
        .drop("idx")
    )


def _metrics(
    portfolio,
    equity: pl.DataFrame,
    rejections: pl.DataFrame,
    config: BacktestConfig,
) -> dict[str, Any]:
    trades = portfolio.trades.records_arr
    closed = trades[trades["status"] == 1]
    positive = float(np.sum(closed["pnl"][closed["pnl"] > 0]))
    negative = float(-np.sum(closed["pnl"][closed["pnl"] < 0]))
    returns = np.asarray(portfolio.returns())
    sharpe = None
    if config.periods_per_year is not None and len(returns) > 1:
        deviation = float(np.std(returns, ddof=1))
        if deviation > 0:
            sharpe = _finite(
                float(np.mean(returns))
                / deviation
                * math.sqrt(config.periods_per_year)
            )
    return {
        "initial_cash": config.initial_cash,
        "final_equity": float(equity["equity"][-1]),
        "net_pnl": float(portfolio.total_profit()),
        "total_return_pct": float(portfolio.total_return()) * 100,
        "max_drawdown_pct": float(equity["drawdown"].max()) * 100,
        "total_fees": float(np.sum(portfolio.orders.records_arr["fees"])),
        "filled_orders": len(portfolio.orders.records_arr),
        "rejected_orders": rejections.filter(
            pl.col("engine_status") == "rejected",
        ).height,
        "ignored_unfilled_orders": rejections.filter(
            pl.col("engine_status") == "ignored",
        ).height,
        "unfilled_orders": rejections.height,
        "closed_trades": len(closed),
        "open_trades": int(np.sum(trades["status"] == 0)),
        "realized_pnl": float(np.sum(closed["pnl"])),
        "open_trade_pnl": float(np.sum(trades["pnl"][trades["status"] == 0])),
        "closed_win_rate_pct": float(np.mean(closed["pnl"] > 0)) * 100
        if len(closed)
        else None,
        "profit_factor": _finite(positive / negative) if negative else None,
        "sharpe_ratio": sharpe,
        "metric_notes": {
            "profit_factor": None if negative else "No losing closed trades",
            "closed_win_rate_pct": None if len(closed) else "No closed trades",
            "sharpe_ratio": None
            if sharpe is not None
            else "Requires periods_per_year and nonzero finite variance",
        },
    }


def _tag(frame: pl.DataFrame, scope: str, instrument: str) -> pl.DataFrame:
    return frame.with_columns(
        pl.lit(scope).alias("scope"),
        pl.lit(instrument).alias("instrument_id"),
    )


def run_backtest(
    bars: pl.DataFrame,
    positions: pl.DataFrame,
    config: BacktestConfig,
    *,
    scope: str = "full",
    start_ns: int | None = None,
) -> BacktestRun:
    if start_ns is not None:
        bars = bars.filter(pl.col("open_ts").cast(pl.Int64) >= start_ns)
        positions = positions.filter(
            pl.col("decision_ts").cast(pl.Int64) >= start_ns
        )
    if bars.height == 0:
        raise RetaError(
            "insufficient_evidence", "No bars inside backtest scope"
        )
    unknown = set(positions["instrument_id"].unique()) - set(
        bars["instrument_id"].unique()
    )
    if unknown:
        raise RetaError(
            "invalid_backtest_target", "Target instrument has no bars"
        )
    summaries, equities, orders, trades, rejections = [], [], [], [], []
    for instrument_bars in bars.sort(
        ["instrument_id", "open_ts"]
    ).partition_by(
        "instrument_id",
        maintain_order=True,
    ):
        instrument = instrument_bars["instrument_id"][0]
        targets = positions.filter(pl.col("instrument_id") == instrument)
        timeline, pending = _timeline(instrument_bars, targets)
        portfolio = _simulate(timeline, config)
        equity = _equity(portfolio, timeline, config.initial_cash)
        rejected = _rejections(portfolio, timeline)
        summaries.append(
            {
                "instrument_id": instrument,
                "bars": timeline.height,
                "start_ts": _stamp(timeline["open_ts"], 0),
                "end_ts": _stamp(timeline["close_ts"], -1),
                "pending_targets": pending,
                "decision_count": targets.height,
                "status": "completed_with_unfilled_targets"
                if rejected.height
                else "completed",
                **_metrics(portfolio, equity, rejected, config),
            }
        )
        equities.append(_tag(equity, scope, instrument))
        orders.append(_tag(_orders(portfolio, timeline), scope, instrument))
        trades.append(_tag(_trades(portfolio, timeline), scope, instrument))
        rejections.append(_tag(rejected, scope, instrument))
    return BacktestRun(
        {"scope": scope, "starts_flat": True, "instruments": summaries},
        pl.concat(equities),
        pl.concat(orders),
        pl.concat(trades),
        pl.concat(rejections),
    )


def export_backtests(
    directory: Path,
    bars: pl.DataFrame,
    positions: pl.DataFrame,
    config: BacktestConfig,
    *,
    test_start_ns: int | None = None,
) -> dict[str, Any]:
    import vectorbt as vbt

    runs = [run_backtest(bars, positions, config)]
    if test_start_ns is not None:
        runs.append(
            run_backtest(
                bars,
                positions,
                config,
                scope="held_out",
                start_ns=test_start_ns,
            )
        )
    result = {
        "schema_version": "1",
        "status": "completed",
        "engine": {
            "name": "vectorbt",
            "version": vbt.__version__,
            "simulation": "Portfolio.from_orders",
        },
        "config": config.model_dump(mode="json"),
        "scopes": [run.summary for run in runs],
        "held_out_start_ns": test_start_ns,
        "assumptions": [
            "Targets fill at effective opens; equity is marked at bar closes",
            "Latest decision wins at a shared effective opening",
            "Unobserved terminal opens stay pending; no forced liquidation",
            "Independent flat cash books; initial capital per instrument",
            "Integer units, linear unit payoff, one-times short cash locking",
            "No leverage, multipliers, funding, borrow, FX, dividends "
            "or liquidation model",
            "Configured costs are illustrative, not inferred provider costs",
            "Vectorbt exit trades; win metrics use closed trades",
            "Financial results do not change behavioral model promotion",
        ],
    }
    for name in ["equity", "orders", "trades", "rejections"]:
        pl.concat([getattr(run, name) for run in runs]).write_parquet(
            directory / f"backtest_{name}.parquet",
        )
    write_json(directory / "backtest.json", result)
    return result
