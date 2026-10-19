"""Behavioral fidelity, explicit support and deterministic event matching."""

from collections import defaultdict, deque
from typing import Any

import polars as pl

from reta.contracts import EvaluationPolicy


def macro_f1(frame: pl.DataFrame) -> float | None:
    if frame.height == 0:
        return None
    scores = []
    actual = pl.col("direction")
    predicted = pl.col("target_units").sign()
    for label in frame["direction"].unique().to_list():
        true_positive = frame.filter(
            (actual == label) & (predicted == label),
        ).height
        false_positive = frame.filter(
            (actual != label) & (predicted == label),
        ).height
        false_negative = frame.filter(
            (actual == label) & (predicted != label),
        ).height
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(2 * true_positive / denominator if denominator else 0)
    return sum(scores) / len(scores)


def _events(frame: pl.DataFrame, column: str) -> list[tuple[int, int, int]]:
    previous = pl.col(column).shift(1)
    known_pair = pl.col("direction").is_not_null() & (
        pl.col("direction").shift(1).is_not_null()
    )
    rows = (
        frame.with_row_index("ordinal")
        .with_columns(
            previous.alias("previous"),
        )
        .filter(known_pair & (pl.col(column) != previous))
    )
    return rows.select("ordinal", "previous", column).rows()


def transition_metrics(
    frame: pl.DataFrame,
    tolerance: int,
) -> dict[str, int | float | None]:
    frame = frame.with_columns(
        pl.col("target_units").sign().alias("predicted_direction"),
    )
    actual = _events(frame, "direction")
    predicted = _events(frame, "predicted_direction")
    grouped: dict[tuple[int, int], deque[int]] = defaultdict(deque)
    for ordinal, previous, current in predicted:
        grouped[(previous, current)].append(ordinal)
    matched = 0
    for ordinal, previous, current in actual:
        candidates = grouped[(previous, current)]
        while candidates and candidates[0] < ordinal - tolerance:
            candidates.popleft()
        if candidates and candidates[0] <= ordinal + tolerance:
            candidates.popleft()
            matched += 1
    denominator = len(actual) + len(predicted)
    value = 2 * matched / denominator if actual else None
    return {
        "transition_f1": value,
        "observed_transitions": len(actual),
        "predicted_transitions": len(predicted),
        "matched_transitions": matched,
    }


def measure(frame: pl.DataFrame, tolerance: int) -> dict[str, Any]:
    known = frame.filter(pl.col("direction").is_not_null())
    quantity_known = known.filter(pl.col("quantity_units").is_not_null())
    error = None
    if quantity_known.height:
        error = quantity_known.select(
            (pl.col("target_units") - pl.col("quantity_units")).abs().mean()
            / pl.max_horizontal(1, pl.col("quantity_units").abs().mean()),
        ).item()
    return {
        "points": known.height,
        "expected_points": frame.height,
        "coverage": known.height / frame.height if frame.height else 0,
        "quantity_points": quantity_known.height,
        "classes": known["direction"].n_unique(),
        "macro_f1": macro_f1(known),
        "normalized_position_mae": error,
        **transition_metrics(frame, tolerance),
    }


def assess(
    metrics: dict[str, Any],
    policy: EvaluationPolicy,
    *,
    claim: str,
    baseline: float,
) -> tuple[str, list[str]]:
    missing = []
    if metrics["coverage"] < policy.minimum_coverage:
        missing.append("minimum_coverage")
    if metrics["points"] < policy.minimum_points:
        missing.append("minimum_points")
    if metrics["classes"] < policy.minimum_classes:
        missing.append("minimum_classes")
    if metrics["observed_transitions"] < policy.minimum_transitions:
        missing.append("minimum_transitions")
    if (
        claim == "absolute_positions"
        and metrics["quantity_points"] != metrics["points"]
    ):
        missing.append("known_absolute_sizes")
    if missing:
        return "insufficient_evidence", missing
    failures = []
    if metrics["macro_f1"] < policy.minimum_macro_f1:
        failures.append("minimum_macro_f1")
    if metrics["transition_f1"] < policy.minimum_transition_f1:
        failures.append("minimum_transition_f1")
    if metrics["macro_f1"] < baseline + policy.minimum_baseline_improvement:
        failures.append("minimum_baseline_improvement")
    if (
        claim == "absolute_positions"
        and metrics["normalized_position_mae"] > policy.maximum_position_mae
    ):
        failures.append("maximum_position_mae")
    return ("no_candidate_passed", failures) if failures else ("succeeded", [])
