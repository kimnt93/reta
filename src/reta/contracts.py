"""Validated boundaries for alpha research and explicit-rule conversion."""

from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RetaError(Exception):
    """A safe user-facing diagnostic, never a raw credential payload."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        allow_inf_nan=False,
    )


class AlphaSpec(Contract):
    schema_version: Literal["1"] = "1"
    strategy_id: str = Field(default="alpha", pattern=r"^[\w.-]+$")
    family: Literal["sma_regime", "channel_breakout", "zscore_reversion"]
    lookback: int = Field(ge=2, le=10000)
    exit_lookback: int = Field(default=2, ge=1)
    band_bps: float = Field(default=0, ge=0, allow_inf_nan=False)
    entry_z: float = Field(default=1.5, gt=0, allow_inf_nan=False)
    exit_z: float = Field(default=0.5, ge=0, allow_inf_nan=False)
    units: int = Field(default=1, ge=1, le=1_000_000_000)
    allow_short: bool = True
    latency_ns: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_family(self) -> Self:
        if (
            self.family == "channel_breakout"
            and self.exit_lookback > self.lookback
        ):
            raise ValueError("exit_lookback exceeds lookback")
        if self.family == "zscore_reversion" and self.exit_z >= self.entry_z:
            raise ValueError("exit_z must be below entry_z")
        return self


class EvaluationPolicy(Contract):
    train_fraction: float = Field(default=0.6, gt=0, lt=1)
    validation_fraction: float = Field(default=0.2, gt=0, lt=1)
    minimum_points: int = Field(default=50, ge=1)
    minimum_transitions: int = Field(default=10, ge=1)
    minimum_classes: int = Field(default=2, ge=2, le=3)
    minimum_coverage: float = Field(default=0.95, gt=0, le=1)
    minimum_macro_f1: float = Field(default=0.8, ge=0, le=1)
    minimum_transition_f1: float = Field(default=0.7, ge=0, le=1)
    maximum_position_mae: float = Field(default=0.1, ge=0)
    minimum_baseline_improvement: float = Field(default=0.05, ge=0)
    timing_tolerance_bars: int = Field(default=1, ge=0)

    @model_validator(mode="after")
    def check_split(self) -> Self:
        if self.train_fraction + self.validation_fraction >= 1:
            raise ValueError("fractions must leave a nonempty test set")
        return self


class BacktestConfig(Contract):
    """Illustrative cash-book assumptions, not inferred broker conditions."""

    initial_cash: float = Field(default=100_000, gt=0)
    currency: str = Field(default="quote", min_length=1, max_length=16)
    fees_bps: float = Field(default=5, ge=0, lt=10_000)
    fixed_fee: float = Field(default=0, ge=0)
    slippage_bps: float = Field(default=2, ge=0, lt=10_000)
    periods_per_year: float | None = Field(default=None, gt=0)


class ResearchRequest(Contract):
    schema_version: Literal["1"] = "1"
    objective: str = Field(min_length=1)
    bars: Path
    observations: Path
    observation_kind: Literal[
        "positions", "signals", "executions", "round_trips", "pnl", "equity"
    ] = "positions"
    claim: Literal["direction", "absolute_positions"] = "absolute_positions"
    source_type: Literal[
        "live", "paper", "backtest", "model_account", "synthetic", "unknown"
    ]
    source_url: str = "local-export"
    permission: str = Field(min_length=1)
    complete_history: bool = False
    initial_position: int | None = None
    account_mode: Literal["netting", "hedged", "unknown"] = "netting"
    families: list[
        Literal["sma_regime", "channel_breakout", "zscore_reversion"]
    ] = Field(default_factory=lambda: ["sma_regime", "channel_breakout"])
    candidate_specs: list[AlphaSpec] = Field(default_factory=list)
    max_trials: int = Field(default=100, ge=1, le=10000)
    max_lookback: int = Field(default=50, ge=2, le=10000)
    sizing_units: int = Field(default=1, ge=1)
    evaluation: EvaluationPolicy = Field(default_factory=EvaluationPolicy)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)

    @model_validator(mode="after")
    def check_candidates(self) -> Self:
        if not self.families and not self.candidate_specs:
            raise ValueError("at least one family or candidate is required")
        return self


class ImportMapping(Contract):
    """Explicit provider columns; canonical names are never guessed."""

    columns: dict[str, str]
    timezone: str = "UTC"
