"""Canonical frames, UTC validation and evidence-aware position labels."""

import json
from pathlib import Path

import polars as pl

from reta.contracts import ImportMapping, ResearchRequest, RetaError

TIME_TYPE = pl.Datetime("ns", "UTC")
BAR_FIELDS = [
    "instrument_id",
    "open_ts",
    "close_ts",
    "available_ts",
    "next_open_ts",
    "open",
    "high",
    "low",
    "close",
]


def read_frame(path: Path) -> pl.DataFrame:
    if path.suffix == ".parquet":
        return pl.read_parquet(path)
    if path.suffix == ".csv":
        return pl.read_csv(path, infer_schema_length=10000)
    value = json.loads(path.read_text())
    if isinstance(value, dict):
        value = value["rows"]
    return pl.DataFrame(value)


def timestamps(frame: pl.DataFrame, names: list[str]) -> pl.DataFrame:
    expressions = []
    for name in names:
        if frame.schema[name] == pl.String:
            zoned = pl.col(name).str.contains(r"(Z|[+-]\d{2}:\d{2})$")
            if has_any(frame, ~zoned):
                raise RetaError(
                    "missing_timezone", f"Explicit zone required: {name}"
                )
            expression = pl.col(name).str.to_datetime(
                time_unit="ns",
                time_zone="UTC",
                strict=True,
            )
        else:
            if not isinstance(frame.schema[name], pl.Datetime):
                raise RetaError("invalid_time", f"Expected UTC time: {name}")
            if frame.schema[name].time_zone is None:
                raise RetaError("missing_timezone", f"Naive time: {name}")
            expression = pl.col(name).cast(TIME_TYPE)
        expressions.append(expression.alias(name))
    return frame.with_columns(expressions)


def require_columns(frame: pl.DataFrame, names: list[str]) -> None:
    missing = sorted(set(names) - set(frame.columns))
    if missing:
        raise RetaError("missing_columns", ", ".join(missing))


def has_any(frame: pl.DataFrame, condition: pl.Expr) -> bool:
    return bool(frame.select(condition.fill_null(False).any()).item())


def load_bars(path: Path) -> pl.DataFrame:
    frame = read_frame(path)
    require_columns(frame, BAR_FIELDS)
    frame = timestamps(
        frame,
        ["open_ts", "close_ts", "available_ts", "next_open_ts"],
    ).sort(["instrument_id", "open_ts"])
    if frame.height == 0:
        raise RetaError("empty_bars", "No final market bars")
    if frame.select(pl.sum_horizontal(pl.col(BAR_FIELDS).null_count())).item():
        raise RetaError("missing_bar_values", "Market bars contain nulls")
    validate_bar_prices(frame)
    validate_bar_schedule(frame)
    return frame


def validate_bar_prices(frame: pl.DataFrame) -> None:
    prices = ["open", "high", "low", "close"]
    if has_any(frame, ~pl.all_horizontal(pl.col(prices).is_finite())):
        raise RetaError("invalid_price", "Nonfinite market price")
    if has_any(frame, pl.min_horizontal(prices) <= 0):
        raise RetaError("invalid_price", "Nonpositive market price")
    if has_any(frame, pl.col("high") < pl.max_horizontal("open", "close")):
        raise RetaError("invalid_ohlc", "High below open or close")
    if has_any(frame, pl.col("low") > pl.min_horizontal("open", "close")):
        raise RetaError("invalid_ohlc", "Low above open or close")
    if "is_final" in frame.columns:
        invalid = ~pl.col("is_final").fill_null(False)
        if has_any(frame, invalid):
            raise RetaError("nonfinal_bar", "Only final bars are supported")


def validate_bar_schedule(frame: pl.DataFrame) -> None:
    key = ["instrument_id", "open_ts"]
    if frame.unique(subset=key).height != frame.height:
        raise RetaError("duplicate_bar", "Duplicate instrument/open key")
    if has_any(frame, pl.col("close_ts") <= pl.col("open_ts")):
        raise RetaError("invalid_schedule", "Bar must close after opening")
    if has_any(frame, pl.col("available_ts") < pl.col("close_ts")):
        raise RetaError("invalid_availability", "Final bar known before close")
    if has_any(frame, pl.col("next_open_ts") < pl.col("close_ts")):
        raise RetaError("invalid_schedule", "Next opening precedes close")
    next_observed = pl.col("open_ts").shift(-1).over("instrument_id")
    if has_any(frame, next_observed != pl.col("next_open_ts")):
        raise RetaError("bar_gap", "Missing or conflicting scheduled bar")
    previous = pl.col("available_ts").shift(1).over("instrument_id")
    if has_any(frame, pl.col("available_ts") <= previous):
        raise RetaError("out_of_order_availability", "Bar availability order")


def import_table(
    source: Path,
    mapping: ImportMapping,
    destination: Path,
) -> dict[str, object]:
    frame = read_frame(source)
    require_columns(frame, list(mapping.columns.values()))
    frame = frame.select(
        [
            pl.col(original).alias(canonical)
            for canonical, original in mapping.columns.items()
        ]
    )
    for name in frame.columns:
        if not name.endswith("_ts"):
            continue
        if frame.schema[name] != pl.String:
            continue
        frame = frame.with_columns(
            pl.col(name)
            .str.to_datetime(
                time_unit="ns",
                time_zone=mapping.timezone,
                strict=True,
            )
            .dt.convert_time_zone("UTC"),
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RetaError("output_exists", "Import destination already exists")
    frame.write_parquet(destination)
    destination.chmod(0o600)
    return {"path": str(destination), "rows": frame.height}


def labels_for(
    request: ResearchRequest,
    observations: pl.DataFrame,
) -> pl.DataFrame:
    kind = request.observation_kind
    if kind in {"pnl", "equity"}:
        raise RetaError(
            "insufficient_evidence",
            "PnL/equity does not identify positions",
        )
    if request.account_mode != "netting":
        raise RetaError("unsupported_account", "Netting evidence is required")
    require_columns(observations, ["instrument_id"])
    if kind in {"executions", "round_trips"}:
        return execution_labels(request, observations)
    require_columns(observations, ["event_ts"])
    require_values(observations, ["instrument_id", "event_ts"])
    frame = timestamps(observations, ["event_ts"])
    if "target_units" in frame.columns:
        validate_integer(frame, "target_units", positive=False)
        frame = frame.with_columns(
            pl.col("target_units").cast(pl.Int64).alias("quantity_units"),
        )
    elif "direction" in frame.columns:
        if has_any(
            frame,
            ~pl.col("direction").cast(pl.Float64).is_in([-1.0, 0.0, 1.0]),
        ):
            raise RetaError("invalid_direction", "Expected -1, 0, or 1")
        frame = frame.with_columns(
            pl.lit(None, pl.Int64).alias(
                "quantity_units",
            )
        )
    else:
        raise RetaError("missing_columns", "Need target_units or direction")
    return finish_labels(frame)


def validate_integer(
    frame: pl.DataFrame,
    name: str,
    *,
    positive: bool,
) -> None:
    value = pl.col(name).cast(pl.Float64)
    if has_any(frame, ~value.is_finite()):
        raise RetaError("invalid_quantity", "Nonfinite quantity")
    if has_any(frame, value != value.floor()):
        raise RetaError(
            "unsupported_quantity", "Integer native units required"
        )
    if has_any(frame, value.abs() > 1_000_000_000):
        raise RetaError(
            "unsupported_quantity", "Native size exceeds engine limit"
        )
    if positive and has_any(frame, value <= 0):
        raise RetaError("invalid_quantity", "Quantity must be positive")


def execution_labels(
    request: ResearchRequest,
    observations: pl.DataFrame,
) -> pl.DataFrame:
    if request.initial_position is None:
        raise RetaError("insufficient_evidence", "Initial position is unknown")
    if not request.complete_history:
        raise RetaError(
            "insufficient_evidence", "Execution coverage is unknown"
        )
    if request.observation_kind == "round_trips":
        observations = round_trip_events(observations)
    require_columns(observations, ["event_ts", "side", "quantity"])
    require_values(observations, ["instrument_id", "event_ts", "side"])
    observations = deduplicate_events(observations)
    validate_integer(observations, "quantity", positive=True)
    if observations["quantity"].null_count():
        raise RetaError("insufficient_evidence", "Execution size is hidden")
    observations = observations.with_columns(pl.col("quantity").cast(pl.Int64))
    if has_any(observations, ~pl.col("side").is_in(["buy", "sell"])):
        raise RetaError("invalid_side", "Expected buy or sell")
    frame = timestamps(observations, ["event_ts"])
    frame = frame.with_columns(
        pl.when(pl.col("side") == "buy")
        .then(pl.col("quantity"))
        .otherwise(-pl.col("quantity"))
        .cast(pl.Int64)
        .alias("delta"),
    )
    frame = (
        frame.group_by(["instrument_id", "event_ts"])
        .agg(
            pl.col("delta").sum(),
        )
        .sort(["instrument_id", "event_ts"])
    )
    frame = frame.with_columns(
        (
            pl.col("delta").cum_sum().over("instrument_id")
            + request.initial_position
        ).alias("quantity_units"),
    )
    return finish_labels(frame)


def round_trip_events(frame: pl.DataFrame) -> pl.DataFrame:
    require_columns(
        frame,
        [
            "instrument_id",
            "entry_ts",
            "exit_ts",
            "direction",
            "quantity",
        ],
    )
    frame = timestamps(frame, ["entry_ts", "exit_ts"])
    require_values(
        frame, ["instrument_id", "entry_ts", "exit_ts", "direction"]
    )
    if has_any(frame, pl.col("exit_ts") <= pl.col("entry_ts")):
        raise RetaError("invalid_trade", "Exit must follow entry")
    if has_any(
        frame, ~pl.col("direction").cast(pl.Float64).is_in([-1.0, 1.0])
    ):
        raise RetaError(
            "invalid_direction", "Round trips need signed direction"
        )
    frame = frame.with_columns(pl.col("direction").cast(pl.Int8))
    entry = frame.select(
        "instrument_id",
        pl.col("entry_ts").alias("event_ts"),
        "quantity",
        pl.when(pl.col("direction") == 1)
        .then(pl.lit("buy"))
        .otherwise(pl.lit("sell"))
        .alias("side"),
    )
    exit_frame = frame.select(
        "instrument_id",
        pl.col("exit_ts").alias("event_ts"),
        "quantity",
        pl.when(pl.col("direction") == 1)
        .then(pl.lit("sell"))
        .otherwise(pl.lit("buy"))
        .alias("side"),
    )
    return pl.concat([entry, exit_frame])


def finish_labels(frame: pl.DataFrame) -> pl.DataFrame:
    if "direction" in frame.columns:
        if has_any(
            frame,
            ~pl.col("direction").cast(pl.Float64).is_in([-1.0, 0.0, 1.0]),
        ):
            raise RetaError("invalid_direction", "Expected -1, 0, or 1")
        frame = frame.with_columns(pl.col("direction").cast(pl.Int8))
        disagreement = pl.col("quantity_units").sign() != pl.col("direction")
        if has_any(frame, disagreement):
            raise RetaError(
                "contradictory_label", "Direction and quantity disagree"
            )
    if "direction" not in frame.columns:
        frame = frame.with_columns(
            pl.col("quantity_units").sign().cast(pl.Int8).alias("direction"),
        )
    if "position_known" in frame.columns:
        if frame.schema["position_known"] != pl.Boolean:
            raise RetaError(
                "invalid_known_flag", "position_known must be Boolean"
            )
        frame = frame.with_columns(
            pl.when(pl.col("position_known"))
            .then(pl.col("direction"))
            .otherwise(None)
            .alias("direction"),
            pl.when(pl.col("position_known"))
            .then(pl.col("quantity_units"))
            .otherwise(None)
            .alias("quantity_units"),
        )
    key = ["instrument_id", "event_ts"]
    if frame.unique(subset=key).height != frame.height:
        raise RetaError("ambiguous_labels", "Duplicate label instants")
    return frame.select(
        *key,
        "quantity_units",
        "direction",
    ).sort(key)


def align_labels(
    positions: pl.DataFrame,
    labels: pl.DataFrame,
    *,
    continuous: bool,
) -> pl.DataFrame:
    if continuous:
        return positions.join_asof(
            labels,
            left_on="effective_ts",
            right_on="event_ts",
            by="instrument_id",
            strategy="backward",
            check_sortedness=False,
        )
    return positions.join(
        labels,
        left_on=["instrument_id", "effective_ts"],
        right_on=["instrument_id", "event_ts"],
        how="left",
    )


def require_values(frame: pl.DataFrame, names: list[str]) -> None:
    if frame.select(pl.sum_horizontal(pl.col(names).null_count())).item():
        raise RetaError(
            "missing_identity", "Observation identity/time is missing"
        )


def deduplicate_events(frame: pl.DataFrame) -> pl.DataFrame:
    if "event_id" not in frame.columns:
        return frame
    require_values(frame, ["event_id"])
    identity = ["instrument_id", "event_id"]
    distinct = frame.unique()
    if distinct.unique(subset=identity).height != distinct.height:
        raise RetaError(
            "conflicting_event", "Event ID has conflicting records"
        )
    return distinct
