"""Trusted, standalone Polars alpha kernel; no I/O during generation.

This file is exported verbatim as model.py. It intentionally imports no RETA
modules, contains no eval, and requires only Polars for standalone replay.
"""

import argparse
import json
from collections.abc import Mapping
from pathlib import Path

import polars as pl


def _sma(frame: pl.LazyFrame, spec: Mapping) -> pl.LazyFrame:
    frame = frame.with_columns(
        pl.col("close")
        .rolling_mean(spec["lookback"])
        .over("instrument_id")
        .alias("reference"),
    )
    band = spec["band_bps"] / 10000
    return frame.with_columns(
        pl.when(pl.col("close") > pl.col("reference") * (1 + band))
        .then(1)
        .when(pl.col("close") < pl.col("reference") * (1 - band))
        .then(-1)
        .otherwise(0)
        .cast(pl.Int8)
        .alias("state"),
    )


def _reversion(frame: pl.LazyFrame, spec: Mapping) -> pl.LazyFrame:
    frame = frame.with_columns(
        pl.col("close")
        .rolling_mean(spec["lookback"])
        .over("instrument_id")
        .alias("reference"),
        pl.col("close")
        .rolling_std(spec["lookback"], ddof=0)
        .over("instrument_id")
        .alias("deviation"),
    )
    frame = frame.with_columns(
        pl.when(pl.col("deviation") == 0)
        .then(0)
        .otherwise(
            (pl.col("close") - pl.col("reference")) / pl.col("deviation")
        )
        .alias("z"),
    )
    return frame.with_columns(
        pl.when(pl.col("z") <= -spec["entry_z"])
        .then(1)
        .when(pl.col("z") >= spec["entry_z"])
        .then(-1)
        .when(pl.col("z").abs() <= spec["exit_z"])
        .then(0)
        .otherwise(None)
        .cast(pl.Int8)
        .alias("state"),
    )


def _channel(frame: pl.LazyFrame, spec: Mapping) -> pl.LazyFrame:
    frame = frame.with_columns(
        pl.col("high")
        .shift(1)
        .rolling_max(spec["lookback"])
        .over("instrument_id")
        .alias("upper"),
        pl.col("low")
        .shift(1)
        .rolling_min(spec["lookback"])
        .over("instrument_id")
        .alias("reference"),
        pl.col("high")
        .shift(1)
        .rolling_max(spec["exit_lookback"])
        .over("instrument_id")
        .alias("exit_high"),
        pl.col("low")
        .shift(1)
        .rolling_min(spec["exit_lookback"])
        .over("instrument_id")
        .alias("exit_low"),
    )
    frame = frame.with_columns(
        pl.when(pl.col("close") > pl.col("upper"))
        .then(1)
        .when(pl.col("close") < pl.col("reference"))
        .then(-1)
        .otherwise(None)
        .cast(pl.Int8)
        .alias("entry"),
    ).with_columns(
        pl.col("entry")
        .forward_fill()
        .over("instrument_id")
        .alias("last_entry"),
    )
    long_exit = (pl.col("last_entry") == 1) & (
        pl.col("close") < pl.col("exit_low")
    )
    short_exit = (pl.col("last_entry") == -1) & (
        pl.col("close") > pl.col("exit_high")
    )
    return frame.with_columns(
        pl.when(pl.col("entry").is_not_null())
        .then(pl.col("entry"))
        .when(long_exit | short_exit)
        .then(0)
        .otherwise(None)
        .cast(pl.Int8)
        .alias("state"),
    )


def generate_positions(
    bars: pl.LazyFrame,
    *,
    spec: Mapping,
) -> pl.LazyFrame:
    """Generate absolute targets using only final, causally available bars.

    Inputs must be canonical validated bars with explicit next_open_ts.
    Model validation and artifact integrity are enforced by the RETA CLI.
    """
    bars = bars.with_columns(
        pl.col(["open_ts", "close_ts", "available_ts", "next_open_ts"]).cast(
            pl.Datetime("ns", "UTC")
        ),
    )
    frame = bars.sort(["instrument_id", "open_ts"])
    family = spec["family"]
    functions = {
        "sma_regime": _sma,
        "channel_breakout": _channel,
        "zscore_reversion": _reversion,
    }
    if family not in functions:
        raise ValueError("Unsupported alpha family")
    frame = functions[family](frame, spec)
    frame = frame.filter(pl.col("reference").is_not_null())
    frame = frame.with_columns(
        pl.col("state")
        .forward_fill()
        .over("instrument_id")
        .fill_null(0)
        .alias("state"),
    )
    if not spec["allow_short"]:
        frame = frame.with_columns(pl.col("state").clip(0, 1))
    frame = frame.with_columns(
        (
            pl.col("available_ts")
            + pl.duration(
                nanoseconds=spec["latency_ns"],
            )
        ).alias("decision_ts"),
    )
    frame = _effective_times(frame, bars)
    return frame.select(
        pl.lit(spec["strategy_id"]).alias("strategy_id"),
        "instrument_id",
        "decision_ts",
        "effective_ts",
        (pl.col("state") * spec["units"]).cast(pl.Int64).alias("target_units"),
        pl.col("state").cast(pl.Int8).alias("signal_state"),
        pl.when(pl.col("state") == 1)
        .then(pl.lit("long"))
        .when(pl.col("state") == -1)
        .then(pl.lit("short"))
        .otherwise(pl.lit("flat"))
        .alias("reason_code"),
        pl.lit("1").alias("model_version"),
    ).sort(["instrument_id", "decision_ts"])


def _effective_times(
    frame: pl.LazyFrame,
    bars: pl.LazyFrame,
) -> pl.LazyFrame:
    schedule = (
        pl.concat(
            [
                bars.select(
                    "instrument_id", pl.col("open_ts").alias("effective_ts")
                ),
                bars.select(
                    "instrument_id",
                    pl.col("next_open_ts").alias("effective_ts"),
                ),
            ]
        )
        .unique()
        .sort(["instrument_id", "effective_ts"])
    )
    return frame.sort(["instrument_id", "decision_ts"]).join_asof(
        schedule,
        left_on="decision_ts",
        right_on="effective_ts",
        by="instrument_id",
        strategy="forward",
        check_sortedness=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay this exported alpha")
    parser.add_argument("--bars", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path(__file__).with_name("spec.json"),
    )
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text())
    frame = generate_positions(pl.scan_parquet(args.bars), spec=spec).collect()
    if frame["effective_ts"].null_count():
        parser.error("Schedule does not cover delayed decisions")
    if args.output.exists():
        parser.error("Output already exists")
    frame.write_parquet(args.output)
    print(json.dumps({"positions": frame.height, "path": str(args.output)}))


if __name__ == "__main__":
    main()
