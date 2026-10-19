"""Redistributable synthetic evidence for actual CLI smoke exercises."""

import math
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import polars as pl

from reta.artifacts import write_json
from reta.contracts import AlphaSpec
from reta.models import positions_for
from reta.research import reverse


def create_demo(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=False)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    randomizer = random.Random(17)
    closes = [
        100 + 8 * math.sin(index * 0.4) + randomizer.uniform(-2, 2)
        for index in range(2400)
    ]
    opens = [closes[0], *closes[:-1]]
    timestamps = [start + timedelta(hours=index) for index in range(2400)]
    bars = pl.DataFrame(
        {
            "instrument_id": ["fixture:X:USD"] * 2400,
            "open_ts": timestamps,
            "close_ts": [value + timedelta(hours=1) for value in timestamps],
            "available_ts": [
                value + timedelta(hours=1) for value in timestamps
            ],
            "next_open_ts": [
                value + timedelta(hours=1) for value in timestamps
            ],
            "open": opens,
            "close": closes,
        }
    ).with_columns(
        (pl.max_horizontal("open", "close") + 0.1).alias("high"),
        (pl.min_horizontal("open", "close") - 0.1).alias("low"),
        pl.lit(True).alias("is_final"),
    )
    time_columns = ["open_ts", "close_ts", "available_ts", "next_open_ts"]
    bars = bars.with_columns(
        pl.col(time_columns).cast(pl.Datetime("ns", "UTC"))
    )
    bars.write_parquet(directory / "bars.parquet")
    spec = AlphaSpec(family="sma_regime", lookback=5, units=2)
    positions = positions_for(bars, spec)
    observations = positions.select(
        "instrument_id",
        pl.col("effective_ts").alias("event_ts"),
        "target_units",
    )
    observations.write_parquet(directory / "observations.parquet")
    write_json(directory / "explicit-rule.json", spec.model_dump())
    write_json(
        directory / "request.json",
        {
            "objective": "Recover synthetic alpha behavior from positions",
            "bars": "bars.parquet",
            "observations": "observations.parquet",
            "source_type": "synthetic",
            "permission": "Generated public fixture",
            "complete_history": True,
            "sizing_units": 2,
            "families": ["sma_regime", "channel_breakout", "zscore_reversion"],
        },
    )
    return directory / "request.json"


def run_demo(output_root: Path) -> dict[str, Any]:
    import uuid

    request = create_demo(output_root / f"demo-input-{uuid.uuid4().hex[:12]}")
    return reverse(request, output_root)
