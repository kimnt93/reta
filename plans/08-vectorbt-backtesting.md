# 08 — Vectorbt backtests and report semantics

## Decision

Use the pinned vectorbt community engine (`Portfolio.from_orders`) for
financial simulation, keeping Polars as RETA's canonical data layer. NumPy
arrays cross the engine boundary; pandas remains an upstream implementation
detail, not a second feature/label pipeline. Vectorbt 1.1.2 supports the
project's Python range, including the exercised Python 3.14 environment.

Sources: [portfolio API](https://vectorbt.dev/api/portfolio/base/),
[PyPI metadata](https://pypi.org/project/vectorbt/1.1.2/), and
[license](https://github.com/polakowo/vectorbt/blob/master/LICENSE.md).
The community package uses Apache 2.0 with Commons Clause; review its
commercial-use restrictions before selling a service primarily based on it.
No PRO engine or paid data integration is required.

## Execution contract

- Generated values are absolute net integer targets, not order deltas.
- Apply a target at its declared `effective_ts` using the matching actual
  bar's **open**, with close-price marking after that bar. Never use the
  decision bar's earlier open or its close as an execution price.
- Resolve multiple decisions for one effective opening by latest decision
  timestamp; never execute all of them at the same opening.
- A target beyond the last observed opening stays pending. Do not invent a
  final fill, forward-fill an opening price, or force-liquidate the last trade.
  A target inside the observed opening span but absent from its grid is an
  error, not an instruction to skip to a later available price.
- Initial book is flat. Each instrument gets its own cash book and initial
  capital; no shared-cash portfolio allocator, leverage, futures multiplier,
  inverse payoff, funding, borrowing, FX conversion, liquidation or dividends
  are inferred. Input prices and units must already represent the supported
  one-unit linear cash instrument. Report these assumptions explicitly.
- Enforce integer size granularity, one-times short cash locking, no partial
  resizing, and retain unfilled target attempts. Preserve the actual engine
  status: short cash/granularity limits can return ignored SizeZero rather
  than rejected PartialFill. Neither outcome fabricates achieved exposure.
  Unchanged targets matching actual holdings are not unfilled attempts.
  Report strict rejected, ignored-but-unmet and combined unfilled counts.
  These diagnostics never change behavioral-promotion results.

## Configuration

Typed `BacktestConfig`: initial_cash=100000, currency="quote", fees_bps=5,
fixed_fee=0, slippage_bps=2, periods_per_year=null. These costs are illustrative,
not measured provider fees. Initial capital is per instrument. Currency is a
report label, not an FX conversion request. Users may explicitly choose zero
costs and the report must expose that choice.

A reverse request embeds `backtest`. Conversion and standalone bundle
backtesting accept a JSON `--backtest-config` / `--config` file. Annualized
Sharpe requires explicit periods_per_year; absent/degenerate ratios are JSON
null with reasons, not NaN/Infinity or invented zeros. Drawdown includes the
initial-capital peak so initial transaction losses are not omitted.

## Reports and artifacts

Every reverse and conversion report has a Backtesting section and
`backtest.json`. A fitted reverse candidate gets full-history and independently
initialized held-out results after the validation winner has been frozen.
The held-out run includes only decisions at/after the locked test boundary,
starts flat, and cannot inherit training positions or pending training orders.
Historical bars may still warm causal features/model state. No backtest metric
is used for candidate fitting, test-guided tuning, or promotion.

A rejected/insufficiently validated fitted candidate may have diagnostic
backtest results but is explicitly unpromoted. When no executable candidate
could be fitted (for example PnL-only input), report not_run with its actual
reason; do not fabricate a zero-return portfolio.

Persist long-form `backtest_equity.parquet`, `backtest_orders.parquet`,
`backtest_trades.parquet`, and `backtest_rejections.parquet`, labeled by scope
and instrument. The last file includes rejected and ignored-but-unmet requests,
with original engine status and reason. Include configuration, engine/version,
start/end, initial/final capital, PnL/return, maximum drawdown, costs,
closed/open trades, closed-trade win rate/profit factor, Sharpe availability,
unfilled attempts and pending end-of-data targets. Open trades remain
distinguishable from closed trades.
All files participate in the existing bundle hash manifest.

`reta backtest --bundle DIR` backtests a previously exported/promoted model,
optionally with new bars/config, into a new output directory without mutating
its source bundle. It regenerates positions with the trusted spec kernel;
it never executes arbitrary bundled model source. Outputs and reports remain
local/Git-ignored under output/.

## Acceptance

Exercise hand-checkable long/short reversals and fee/slippage accounting;
zero/unchanged targets; pending last targets; same-opening decision collisions;
insufficient capital without partial fills; open-trade end marks; irregular
schedules; independent instruments; and fresh held-out capital/no training
exposure. Reports must contain actual computed financial results, with
behavioral fidelity kept separate. Smoke reverse, convert and standalone
backtest commands using the installed engine, not a mock or hand-written
replacement simulator.

## Delivery evidence

- Pinned and installed vectorbt 1.1.2 under Python 3.14.7; the adapter uses
  the real Portfolio.from_orders engine, not a replacement simulator.
- `make check`: **38 passing behavioral tests**, Ruff format/lint and
  pycodestyle. Financial regressions cover hand-calculated costs/reversals,
  all-or-nothing capital limits (including engine ignored SizeZero), pending
  opens, fresh held-out capital, independent instruments, unchanged targets,
  and annualized-Sharpe availability/sample-variance boundaries.
- `make demo`: successful synthetic alpha recovery plus actual full and
  held-out backtests. Inspected the generated report's assumptions, return,
  drawdown, costs, trade counts, unfilled attempts and pending-target results.
  The controlled synthetic result is not a real-market performance claim.
- Exercised `reta convert --backtest-config`, `reta backtest --bundle` on
  a pre-backtest bundle with replacement bars/config, `reta inspect` on
  both outputs, and `reta schema --kind backtest`. Conversion and standalone
  reports were inspected; each output verified all 12 hashed artifacts.
- Generated outputs remain private/ignored under output/. Existing bundle
  formats remain readable; standalone backtesting creates a new bundle.
