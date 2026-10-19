# 04 — Model recovery, fitting, and position generation

## 1. The claim to optimize

Recover an executable **behavioral approximation**, not a profitable unrelated
strategy and not the original private code. An LLM provides candidate
explanations and typed specs. Deterministic replay and held-out measurements
determine which explanations survive. Multiple passing models may remain
indistinguishable; report that equivalence set and its disagreements.

| Available evidence | Defensible reconstruction | Claims not justified by that evidence alone |
| --- | --- | --- |
| Complete executions, verified units, known start and market inputs | Net position path, transitions, timing, sizing, execution/PnL consistency | Original indicators, source code, hidden discretionary logic |
| Closed round trips with sizes and known boundary exposure | Interval positions where ledger is complete | Missing partial closes or open positions outside the table |
| Signed signals with timestamps | Observable signal direction/action timing | Actual fills, slippage, realized position sizes |
| Position snapshots | Direction/size at observed points | All intervening entries/exits; no-change assumption without continuity guarantee |
| Prices and directions but hidden sizes | Directional behavior, duration and transition hypotheses | Recovered leverage or absolute sizing |
| Equity/PnL only | Exposure/risk-factor hypotheses under stated assumptions | Unique trades, signals, position path, stops or sizing |
| Description/screenshots only | Candidate hypotheses and collection priorities | Validated executable reconstruction without comparable labels |

If a request requires absolute positions but quantities or units are hidden,
return `insufficient_evidence` for that claim. Direction-only candidates may
be retained as explicitly unpromoted research findings. Narrowing the claim
requires an explicit changed request, not silently weaker gates.

PnL-only research should output an ambiguity report and, optionally, bounded
factor/exposure hypotheses. Do not manufacture a ledger by optimizing toward
one attractive equity curve. If no behavioral labels exist, no model passes
the current behavioral promotion policy.

## 2. Observation-to-label reconstruction

### Netting execution ledger

Sort by account/strategy/instrument, event time and verified source sequence.
Normalize buy quantity to a positive delta and sell to a negative delta.
Given a known starting position `q0`, compute
`q(t) = q0 + cumulative_sum(signed_quantity)` in instrument units.
A partial close changes size, not necessarily direction. A reversal may
close a long and open a short in one fill. Fees/funding change cash/equity,
not signed quantity. Deposits must not be explained as trade profits.

Unknown initial quantity leaves the absolute path unknown until an explicit
complete snapshot/flat state re-anchors it. If simultaneous fills have no
sequence, aggregate the same-time net delta for endpoint labels and mark
intratimestamp order unknown; do not infer stop order from arbitrary row IDs.
Any gap in a guaranteed-complete execution stream breaks continuity until a
new anchor. Never label the interval flat because no row was visible.

A source position snapshot can validate the reconstructed endpoint. A
contradiction is a data-quality failure with evidence refs, not an excuse to
overwrite the source. Initial engine supports netting only. Hedged accounts
retain position IDs/gross legs and must not be treated as a flat book just
because long and short net to zero.

### Other evidence and bar alignment

Round trips become interval labels only with verified quantity, side, time
semantics and completeness. Signals remain signal labels unless their
position effect is explicit. Snapshots constrain only observed points unless
a declared source guarantee establishes a continuous known interval.

Attach labels to declared model evaluation instants, after modeled opening
fills for effective-time positions. Keep time uncertainty/tolerance in the
label manifest; do not shift all observed events until the candidate fits.
A boundary-crossing position and insufficient warmup are separate gaps.
Publication delay affects input availability, not the retrospective event
label's event time. No future/published-later observation may be a feature.

## 3. Trusted StrategySpec grammar

Use [02](02-data-contracts.md) as the authoritative schema. Start with three
finite model families, not arbitrary generated Python:

1. `sma_regime`: trailing SMA over `lookback` final closes, including the
   current closed bar. Long when `close > sma * (1 + band_bps/10000)`;
   short when `close < sma * (1 - band_bps/10000)` if shorting is allowed;
   otherwise flat. Equality and the dead band are flat. A non-positive or
   missing reference invalidates that decision, not a division-by-zero fix.
2. `channel_breakout`: compare current close with highest high/lowest low of
   the **previous** `lookback` closed bars. Enter/reverse long above the
   upper channel or short below the lower channel if permitted. If neither
   entry applies, exit long below the previous `exit_lookback` lowest low;
   exit short above its highest high; otherwise retain state. Entry/reversal
   precedes same-bar exit. Equality does not trigger. Initial state is flat
   unless an explicit compatible ModelContext state is supplied.
3. `zscore_reversion`: trailing mean and population standard deviation
   (`ddof=0`) over `lookback` final closes including current close.
   Long at z <= -entry_z; short at z >= entry_z; exit to flat when
   abs(z) <= exit_z; otherwise retain state. Entry/reversal precedes exit;
   require 0 <= exit_z < entry_z. Zero standard deviation produces a defined
   neutral z=0 only for a truly constant complete window, so it exits/keeps
   flat; missing/nonfinite windows remain invalid.

All include exact parameter bounds, feature lookbacks, state initialization,
shorting constraints, warmup and version. Start fixed integer-unit sizing.
A model with unavailable volume cannot quietly become volume-confirmed.
New families require schemas, causal feature kernels and behavioral checks.
Generic expression strings, Python `eval`, remote packages, and model-chosen
imports are prohibited in the default pipeline.

Stateful rules may use a trusted efficient kernel for unavoidable sequential
state. Keep feature transforms vectorized in Polars; do not run Python
callbacks per market row. A controlled loop over a small candidate list is
not the same as a callback over millions of bars.

## 4. Bounded hypothesis and parameter search

1. Resolve instruments, observation modality, usable label masks, market
   coverage, requested claim and computational budgets.
2. Create and hash the split manifest **before any hypothesis/parameter
   search**. Save exact eligible timestamps and dependency horizons.
3. Produce an evidence dossier from training observations only: holding-time
   distribution, directions, size changes, session patterns, correlations
   with candidate features, gaps, source identity and uncertainty. Do not
   include test trades, future aggregate PnL, or held-out target charts.
4. Host or LLM submits StrategySpec candidates citing supporting/contradicting
   evidence IDs. Automatic mode records provider/model, prompt template
   version, response digest, calls/tokens and sanitized training inputs.
5. Validate grammar, instrument capabilities, permitted inputs, family bounds
   and request limits. Reject invalid specs with explicit diagnostics.
6. Fit bounded discrete grids or seeded random trials. Initial families have
   small explicit parameter spaces; use the simplest deterministic search
   that fits the budget. Charge every evaluated parameter tuple as a trial.
   Repeated prompts/agents share the same total trial/candidate cap.
7. Rank on training/validation only; freeze the shortlist and tie-break by
   fewer parameters, then canonical spec hash. Rejects remain in the ledger.
8. Test the frozen shortlist once with locked gates; never adapt a family,
   tolerance, exclusion mask or threshold after inspecting test results.
   A changed experiment needs a new uncontaminated holdout or forward period.
9. Package passing candidates in frozen validation rank, not test-optimized
   rank. If none pass, publish the no-candidate report and failed dimensions.

Model complexity is constrained by family grammar and parameter budgets.
Initially rank lexicographically by validation direction macro-F1, transition
F1, lower sizing error where applicable, lower complexity, then spec hash.
This prevents a high PnL correlation from buying away a failed behavior gate.

Initial deterministic grids: SMA lookback `[3,5,10,20,50]` and band bps
`[0,10,25]`; channel lookback `[5,10,20,50]` and exit lookback `[2,5,10]`
with exit <= entry lookback; z-score lookback `[10,20,50]`, entry z
`[1,1.5,2]` and exit z `[0,0.5]`. Filter all grids by the request's fixed
`max_lookback_bars` and instrument capabilities before trial zero; an empty
grid is an explicit rejection. Enumerate canonical tuples deterministically
and stop at the shared trial cap. Concrete LLM proposals are initial
hypotheses, not permission to widen these bounds after inspecting test data.
`max_candidates` caps structural hypotheses; `max_fit_trials` caps all
evaluated parameter tuples across them. Fixed units are known from a
declared training-derived size hypothesis or an explicit research sizing
policy; do not infer hidden absolute size from direction-only evidence.

### Temporal split and leakage rules

Default policy proposal: 60% training, 20% validation, 20% final test in time,
with explicit purged boundaries. Fractions do not substitute for support
minima. Exact intervals are stored, not recomputed separately per candidate.
Purges must cover label dependencies crossing a boundary; the configured
`purge_bars` must be at least the declared maximum dependency horizon.
If any label depends on an exit beyond the split, exclude it or purge that
whole dependency. Do not truncate a future-dependent trade label at the split.

Trailing features can read earlier bars for warmup in validation/test, but
cannot refit transformations or read earlier unknown target labels. Features
must have `available_ts <= decision_ts`. Thresholds/normalizers fit only on
training. Maximum allowed lookback is declared before splitting; reject a
candidate whose lookback exceeds available declared warmup.

Where enough history exists, add rolling-origin walk-forward folds inside
train/validation. Keep the final test untouched. If history is too short,
report insufficient support rather than random row splitting or repeatedly
reusing the same small holdout. Report regime/instrument concentration and
survivorship risks separately from measured behavioral fidelity.

## 5. Metrics and promotion gates

Use only known comparable timestamps and disclose the excluded denominator.
First measure support/coverage; then behavior; then economic consistency.
Never treat unavailable metrics as zero or as a pass.

| Metric | Definition |
| --- | --- |
| Known coverage | Eligible known decision labels / expected tradable decisions in requested scored window |
| Direction accuracy | Correct signed-position classes / known direction labels; diagnostic only |
| Direction macro-F1 | Mean class F1 over supported observed classes {-1,0,1}; report confusion matrix and class support; absent observed classes are not synthetic perfect scores |
| Transition precision/recall/F1 | One-to-one matched model/observed direction transitions within locked timing tolerance, same instrument and from/to class |
| Timing error | Absolute event-time difference of matched transitions, in ns and bars; report quantiles with matched count |
| Normalized position MAE | Mean abs(predicted_units-observed_units) / max(1, mean abs(observed_units)) on quantity-known labels |
| Size-change F1 | Matched nonzero position-delta events; separate increases, reductions and reversals where support permits |
| Holding duration error | Absolute duration difference for comparable fully known intervals |
| PnL consistency | Calculated versus reported PnL on aligned comparable accounting basis; a separate economic diagnostic, not behavioral proof |

Transition matching: build edges only for valid same-instrument/class events
within the fixed tolerance. Compute maximum-cardinality one-to-one matching,
then minimum total time error; ties use event IDs. One prediction cannot match
multiple observations. Empty observed/predicted transitions have insufficient
support, not perfect F1. This matters for always-flat or buy-and-hold candidates.

Baselines: always-flat; training-majority direction; buy-and-hold when the
instrument permits; and last-known direction using only past observations
in explicitly diagnostic mode. A source-observation-driven baseline is not
a deployable recovered model and cannot use future/held-out labels. Never
include observed target positions as an input to candidate generation.

Default proposed gates for `absolute_positions`, configurable and frozen:
known coverage >= 0.95; >= 500 eligible test decisions; >= 20 observed direction
transitions; >= 2 observed classes; macro-F1 >= 0.80; transition F1 >= 0.70;
normalized position MAE <= 0.10; macro-F1 >= strongest eligible deployable
baseline + 0.05. Require all applicable requested gates, not their average.
For sparse direction-only evidence define explicit point-based gates and
support in the request; do not inherit an interval coverage claim.

`behavior_and_pnl` additionally requires comparable complete accounting and
explicit PnL error/cost thresholds in its evaluation policy. Without them the
request is invalid. Funding, commissions, FX conversion, dividends and cash
flows must be treated correctly; otherwise PnL is insufficient evidence.
High fidelity does not imply positive returns; a losing original may be
faithfully approximated. Report behavior and profitability separately.

## 6. Causal Python/Polars position contract

Use the entry point and long-form schema in [02](02-data-contracts.md).
Steps for each instrument:

1. Validate unique sorted bar keys, finality, OHLC constraints, expected
   trading-grid coverage and effective-dated instrument/calendar mappings.
2. Build trailing features per instrument in ascending time. Do not let a
   rolling window span unrelated symbols. A breakout channel must be shifted
   one bar before comparing to current close.
3. Set `decision_ts = max(close_ts, available_ts) + latency_ns` for the bar.
   Inputs used by that decision must have been available by that instant.
4. Determine target state/size with no access to future bars or observed
   position labels. Initial fixed sizing is `state * sizing.units`; enforce
   shorting and quantity-step/min/max rules without fitting violations away.
5. Set `effective_ts` to the first scheduled tradable opening **of a later
   bar** at or after `decision_ts`. Use the instrument calendar/schedule,
   not the next observed row after a missing-data gap. The current bar's
   opening is never eligible. At zero modeled latency a close and the next
   opening can share a timestamp; phase ordering is close -> decision ->
   later-bar open. This is an idealized assumption, explicitly recorded.
6. If latency defers multiple decisions to the same opening, the latest
   decision wins; ties use ascending decision sequence. Generated output
   retains every decision; replay coalesces effective-time targets before
   deriving fills, so it cannot trade repeatedly at that same opening.
7. Emit all valid requested decision rows after warmup, including zeros and
   unchanged targets. Do not double-shift signals: output is indexed by its
   decision time, and the simulator uses `effective_ts` exactly once.

The final input bar can emit a target for a future scheduled open; it does
not require the future bar's price to determine that time. This is target
position generation, not proof of a fill. Replay marks it pending if no open
price is in the replay window. It must not use a future close or force-close
at the last available price. Missing schedule or invalid input segments
produce a typed data/capability error, not null/zero positions.

Polars implementation concerns: `scan_parquet`, early projection/filtering,
explicit sorting and partitioned rolling/shift expressions; collect at the
artifact boundary rather than repeatedly per feature. As-of feature joins
use backward availability matching and a staleness tolerance, with explicit
within-group sortedness checks. Official
[join_asof documentation](https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.join_asof.html)
defines backward matching and sortedness requirements. “Nearest” joins can
select future data and are not allowed for causal inputs.

## 7. Exact worked position example

Synthetic fixture, not an observed market result. One continuously tradable
instrument `fixture:X:USD`; one-hour bars; final close available at close;
zero latency; no shorting restriction; fixed sizing 2 units; `sma_regime`
lookback 3, band 0. Bar opens are 00:00 through 06:00 UTC on 2026-01-01;
close times are one hour later. Input closes are `[10,11,12,9,8,10,11]`.
Required schedule includes the next opening at 07:00 UTC.

| Decision UTC | Current close | SMA(3) | target_units | effective_ts UTC | reason_code |
| --- | ---: | ---: | ---: | --- | --- |
| 03:00 | 12 | 11 | 2 | 03:00 | above_band |
| 04:00 | 9 | 10.6666666667 | -2 | 04:00 | below_band |
| 05:00 | 8 | 9.6666666667 | -2 | 05:00 | below_band |
| 06:00 | 10 | 9 | 2 | 06:00 | above_band |
| 07:00 | 11 | 9.6666666667 | 2 | 07:00 | above_band |

The 05:00 row is mandatory although the short target is unchanged. No rows
at 01:00 or 02:00 because the feature window is incomplete. A flat equality
fixture `[10,10,10]` must emit target 0 at 03:00 with `inside_band`.
Changing/appending a future bar cannot change any already emitted decision.
The 07:00 target can remain pending in replay; do not invent its execution.

Partial-close/reversal fixture for ledger reconstruction: start flat; buy
10 @ 100; sell 4 @ 105; sell 8 @ 102. Positions are `[10,6,-2]`; realized gross
PnL is `4*(105-100)+6*(102-100)=32`, and remaining short entry basis is 102.
With fee 1 on each event and immediate fee expensing, total marked equity
change at final price 102 is 29. The reversal is not a close of eight long
units: six close and two open short. Report fee accounting explicitly.

## 8. Replay, PnL, and expanded sizing

Replay derives quantity delta from current simulated position to the latest
eligible target at each opening. The initial slice fills at observed next
open with declared costs, a simplifying model, not broker realism. Long
buys pay positive slippage and sells receive negative slippage. Use explicit
fees and contract multiplier. Compare observed fills with locked time/price
tolerance rather than force-fitting each fill price.

For a linear instrument in settlement currency, mark-to-market change is
held native quantity * multiplier * price change, plus realized/funding
cash effects as applicable, minus costs. External deposits/withdrawals are
removed from trading return accounting. No PnL conversion without a causal
FX rate and declared valuation basis. Intrabar stops/targets cannot be
uniquely ordered from OHLC when both are touched; reject that claim or use
a declared conservative ambiguity scenario, never pick the profitable path.

Later sizing packets add fixed-notional and risk/volatility sizing using
prior available prices/equity/volatility, explicit caps, and rounding toward
zero to valid lot steps. These are research policies until supported by
size evidence. Fractional native quantities use a declared integer quantity
quantum; exact source conversion required. Hedged, portfolio, inverse and
option engines must declare capability and accounting before use. Futures
rolls produce explicit close/reopen events across actual instruments; a
continuous ticker is a feature series only under a stated mapping.

## 9. Model delivery and numerical acceptance

Export a StrategySpec, trusted `model.py`, runtime/dependency lock, instrument
and schedule metadata, split/fit/evaluation evidence, replay positions, and
limitations per [02](02-data-contracts.md). The model performs no web request
or LLM call. Replaying the same bundle and lawful data must reproduce ordered
positions exactly and metrics within declared numeric tolerance.

Required scenarios: exact worked table; equality-to-flat; no future input
influence; per-instrument isolation; one sizing reduction and reversal;
unknown initial state; hidden interval not flat; delayed availability; missing
next-open price pending; gap not skipped; next-session open; shorting denied;
quantity/lot conversion error; cost/PnL accounting; all-flat failure of
transition support; PnL-only no-promotion; exhausted trials with honest
no-candidate outcome. Add deterministic behavioral regressions for these
consumer-visible boundaries as the corresponding engine is implemented.
