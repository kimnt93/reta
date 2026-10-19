# Backtest and interpret the recovered alpha

Read project plan 08 and `uv run reta schema --kind backtest`.

Every reverse report includes full-history and independently initialized
held-out vectorbt simulation of the validation-selected candidate. Financial
metrics do not select parameters, weaken fidelity gates, or promote rejected
candidates. A high return is not evidence of original-source recovery.

## Assumptions to declare

The request's `backtest` object controls initial_cash, currency label,
fees_bps, fixed_fee, slippage_bps and optional periods_per_year. Defaults are
100000 quote units per instrument, fees 5 bps, fixed fee 0 and slippage 2 bps.
These are hypothetical research assumptions, not inferred provider costs.
Set periods_per_year only for a justified sampling/calendar convention.
Undefined ratios remain null with reasons; never replace them with zero.

Generated target_units are absolute net integer exposure. Use actual opens
at effective_ts, with latest decision winning for a shared opening, and mark
at closes. Missing future opening prices are pending, not fills. Do not
force-close the final open trade just to improve statistics. Each instrument
has an independent flat cash book. No leverage, futures multipliers, FX,
funding, borrow, dividends or liquidation are modeled.

Rejected orders and ignored-but-unmet target attempts must be visible.
Vectorbt may report an unfillable short, rounded to zero native units, as
ignored rather than rejected. Inspect both engine status and unfilled counts;
never claim the requested exposure was achieved when it was not. Unchanged
or flat targets matching current holdings are not failures or extra fees.

## Inspect outputs

Read report.md and backtest.json, then drill into backtest_equity.parquet,
backtest_orders.parquet, backtest_trades.parquet and
backtest_rejections.parquet. Scopes and instrument IDs separate records.
Compare total return, net PnL, drawdown, costs, closed/open trade counts,
closed-trade win rate/profit factor, Sharpe availability and pending targets.
Keep closed-trade PnL distinct from open marks.

If no executable model could be fitted (for example PnL-only input), the report
says not_run with a reason. A fitted but unpromoted candidate can have useful
diagnostic backtests; never present that as a promoted reconstruction.

Use `uv run reta backtest --bundle DIR --config FILE` for an existing exported
model, optionally supplying --bars. It creates a new result without mutating
its source, and regenerates positions using the trusted kernel. That command
alone does not establish held-out behavioral fidelity on new data.
