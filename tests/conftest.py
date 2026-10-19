from datetime import UTC, datetime, timedelta

import polars as pl
import pytest


@pytest.fixture
def make_bars():
    def build(closes, instrument="X"):
        start = datetime(2026, 1, 1, tzinfo=UTC)
        times = [
            start + timedelta(hours=index) for index in range(len(closes))
        ]
        opens = [closes[0], *closes[:-1]]
        return pl.DataFrame(
            {
                "instrument_id": [instrument] * len(closes),
                "open_ts": times,
                "close_ts": [value + timedelta(hours=1) for value in times],
                "available_ts": [
                    value + timedelta(hours=1) for value in times
                ],
                "next_open_ts": [
                    value + timedelta(hours=1) for value in times
                ],
                "open": opens,
                "close": closes,
            }
        ).with_columns(
            pl.max_horizontal("open", "close").alias("high"),
            pl.min_horizontal("open", "close").alias("low"),
            pl.col(
                ["open_ts", "close_ts", "available_ts", "next_open_ts"]
            ).cast(pl.Datetime("ns", "UTC")),
        )

    return build
