# 02 — Authoritative data contracts

This document owns names, meanings, and validation rules. Implement typed
contracts once and generate JSON Schemas from them. Reject unknown fields
at fixed metadata boundaries. Connector-specific source payloads belong in
raw artifacts, never extra undeclared top-level fields. Version all contracts
with `schema_version: "1"`; incompatible changes require a new version and
explicit migration, not silent permissive decoding.

## 1. Shared conventions

- IDs are opaque stable strings. `artifact_id` is `sha256:` plus the digest
  of the exact stored bytes. Hash manifests using UTF-8 canonical JSON with
  sorted object keys, compact separators, no NaN/Infinity, and no self-hash.
  Manifest timestamps are outside deterministic semantic identity if they
  represent creation time rather than input data.
- JSON event timestamps: RFC 3339 UTC strings with up to nine fractional
  digits. Parquet: `Datetime(ns, UTC)`. Preserve timestamp precision and
  original zone/offset as source metadata. Never pass ns values through
  microsecond-only datetime conversions. Metadata wall-clock timestamps may
  use microsecond UTC precision.
- `event_ts` describes behavior; `published_ts` describes source publication
  if known; `retrieved_at` describes capture. `available_ts` describes when a
  modeled input was available. Unknown publication is null, not event time.
- Missing means null plus a reason in quality metadata, not zero or NaN.
  Zero quantity/position is an assertion requiring evidence.
- `source_type`: `live`, `paper`, `backtest`, `model_account`, `unknown`.
  `observation_kind`: `signal`, `execution`, `round_trip`, `position_snapshot`,
  `equity_point`, `pnl_point`, `cash_flow`, `description`, `market_bar`.
- A strategy is scoped by `(source_id, source_strategy_id, account_role)`.
  Account roles: `provider`, `subscriber`, `model_account`, `unknown`.
  Never merge provider and follower executions because names match.
- Dataset keys are explicit; frame order is never an identity or time rule.
  Numeric transform columns may use Float64, but exact source prices, sizes,
  and money remain decimal strings/raw values. Normalize exact amounts to
  Decimal(38,12) only after scale/range checks; overflow is an error.

## 2. ResearchRequest

Required fields and nested contracts:

| Field | Type / rule |
| --- | --- |
| `schema_version` | Literal `"1"` |
| `objective` | Non-empty research question; untrusted data, not executable policy |
| `sources` | List of `{url?, platform?, strategy_id?, artifact_ref?}`; each has URL, platform, or artifact reference |
| `universe` | Explicit instrument IDs, or `discover` with `markets` and a finite `max_instruments`; freeze resolution before fitting |
| `window` | `{start, end, timeframe}`; half-open `[start,end)`, start < end |
| `claim` | `direction`, `absolute_positions`, or `behavior_and_pnl`; evidence must support every required dimension |
| `access_policy` | `{free_only:true, allow_free_login, allowed_origins, allowed_import_roots, allow_browser, unattended}` |
| `evidence_policy` | `{allowed_source_types, minimum_coverage, require_known_initial_position, allow_delayed_publication}` |
| `budget` | Integer caps: `max_sources`, `max_pages_per_source`, `max_bytes`, `max_wall_seconds`, `max_llm_calls`, `max_llm_tokens`, `max_candidates`, `max_fit_trials`; zero-LLM exception below |
| `inference` | `{mode, allowed_families, max_lookback_bars, seed}`; mode `host` or `automatic`; positive maximum lookback fixed before splits; provider/model configured outside request secrets |
| `evaluation_policy` | Locked claim gates, split policy, timing tolerance, support minima, baselines; see section 8 and document 04 |

`minimum_coverage` is the fraction of expected tradable decision points with
known comparable labels, not pages fetched. It cannot be measured if the
expected grid is unknown: return a missing-calendar prerequisite. For
point-snapshot evidence report point coverage separately; it does not imply
known continuous intervals. An empty list of sources requires configured
search/registry discovery or explicit import before assessment.

Example request (proposed fixture identifiers and dates, not real data):

```json
{
  "schema_version": "1",
  "objective": "Reconstruct direction and integer-unit positions from an authorized linear-instrument ledger.",
  "sources": [{"artifact_ref": "imports/ledger.csv"}],
  "universe": {"instrument_ids": ["fixture:X:USD"], "markets": [], "max_instruments": 1},
  "window": {"start": "2026-01-01T00:00:00Z", "end": "2026-07-01T00:00:00Z", "timeframe": "1h"},
  "claim": "absolute_positions",
  "access_policy": {"free_only": true, "allow_free_login": false, "allowed_origins": [], "allowed_import_roots": ["imports"], "allow_browser": false, "unattended": true},
  "evidence_policy": {"allowed_source_types": ["paper"], "minimum_coverage": 0.95, "require_known_initial_position": true, "allow_delayed_publication": true},
  "budget": {"max_sources": 3, "max_pages_per_source": 20, "max_bytes": 50000000, "max_wall_seconds": 600, "max_llm_calls": 0, "max_llm_tokens": 0, "max_candidates": 12, "max_fit_trials": 100},
  "inference": {"mode": "host", "allowed_families": ["sma_regime", "channel_breakout"], "max_lookback_bars": 50, "seed": 7},
  "evaluation_policy": {
    "split": {"method": "chronological", "train_fraction": 0.6, "validation_fraction": 0.2, "test_fraction": 0.2, "purge_bars": 50},
    "timing_tolerance_bars": 1,
    "minimum_test_decisions": 500,
    "minimum_test_transitions": 20,
    "minimum_observed_classes": 2,
    "minimum_direction_macro_f1": 0.8,
    "minimum_transition_f1": 0.7,
    "maximum_normalized_position_mae": 0.1,
    "minimum_baseline_improvement": 0.05,
    "required_dimensions": ["direction", "transitions", "sizing"]
  }
}
```

Zero LLM caps are allowed only in `host` mode; all other budget counters
must be positive. In automatic mode the configured provider/model must exist
and both LLM caps must be positive. Thresholds are explicit proposed research
policy, not universal financial truths. Invalid fractions, incompatible claim
and dimensions, or insufficient room for purges fail before search.

For `behavior_and_pnl`, `evaluation_policy.pnl_policy` is required:
`{settlement_currency, commission_bps, slippage_bps, fixed_fee_per_fill,
require_complete_funding, maximum_normalized_pnl_rmse}`. Rates/fees are
nonnegative; normalized PnL RMSE is sqrt(mean squared error of comparable
cash-flow-adjusted cumulative PnL) / max(1, initial account equity in that
currency). Fee/funding basis and initial equity must be known. Other claims
may omit this object; absent cost inputs never imply zero actual costs.

## 3. Discovery and access records

`SourceCandidate`: `candidate_id`, `source_id`, `url`, `source_strategy_id?`,
`markets`, `discovery_method` (`user`, `registry`, `search`, `linked_monitor`),
`evidence_refs`, `claims` (typed documented/observed/unverified statements),
`checked_at`. Descriptions remain untrusted strings.

`AccessProbe`: `probe_id`, candidate identity, `checked_at`, `access_mode`
(`guest`, `free_login`, `user_export`, `paid`, `unknown`), `verdict`
(`approved`, `needs_user_action`, `rejected`, `unknown`), `reason_codes`,
`permission_basis` (policy/terms URL + review evidence), `available_modalities`,
`visible_fields`, `field_semantics`, `history_start?`, `history_end?`,
`reported_total_rows?`, `observed_rows`, `pagination_status`
(`exhausted`, `partial`, `unknown`), `publication_delay?`, `source_type`,
`account_role`, `evidence_refs`, `limitations`, `connector_version`.
No credentials in this record. A `profile_ref` can refer to a local credential
store entry but is stripped from portable bundles. Permission basis cannot
be just "page was accessible". Unknown permission does not authorize capture.

## 4. EvidenceRecord and immutable storage

Required: `evidence_id`, `schema_version`, `run_id`, `source_id`,
`source_strategy_id`, `account_role`, `observation_kind`, `source_type`,
`retrieved_at`, `published_ts?`, `artifact_id`, `locator`, `capture_method`,
`access_probe_id`, `parser_version`, `coverage`, `limitations`, `untrusted:true`.
`locator` identifies a raw JSON pointer, CSV row, DOM table row/screenshot
region, or API page/cursor. `coverage` has `scope`, `status`
(`complete`, `partial`, `unknown`), `window`, `reported_count?`,
`observed_count`, `next_cursor?`, `gaps`. Completeness is relative to declared
scope and window, not the entire provider lifetime.
Local imports create a `user_export` AccessProbe from the supplied permission
basis and import scope before producing EvidenceRecords. This does not claim
the importer visited or authenticated to the original website.

Raw bytes are retained once; evidence records reference them. A redacted
portable derivative has its own hash and a parent reference. Do not claim it
has the original bytes' hash. Headers/cookies are never captured by default;
restricted local originals must not be exposed through public resource reads.

Revisions append new versions linked by `supersedes_evidence_id`; conflicting
versions remain traceable. Deduplicate by source record identity plus content,
not by timestamp/price/quantity alone: identical partial fills can be real.

## 5. Normalized tables

Every normalized row includes `source_id`, `source_strategy_id`,
`account_role`, `source_type`, `evidence_id`, `row_id`, and
`published_ts?`. Stable row IDs derive from source identity and revision.

| Table / key | Required core columns | Important optional columns |
| --- | --- | --- |
| `execution_events` / source-scoped event ID + revision | `event_ts`, `instrument_id`, `side` buy/sell, `quantity` positive decimal, `price` positive decimal, `account_mode` netting/hedged/unknown | `position_id`, `order_id`, `deal_id`, `source_sequence`, `position_effect`, `fee_amount`, `fee_currency`, `realized_pnl`, `pnl_currency` |
| `round_trips` / source trade ID + revision | `instrument_id`, `direction` long/short, `entry_ts`, nullable `exit_ts` | entry/exit price, quantity, fees, PnL, lot IDs; each may be null with missing reason |
| `signal_events` / source signal ID + revision | `instrument_id`, `event_ts`, `action` enter/exit/target/direction, `direction` -1/0/1 where known | target quantity, price, expiry, signal availability and timing uncertainty |
| `position_snapshots` / position ID + snapshot time + revision | `instrument_id`, `event_ts`, `account_mode`, `position_known`, nullable signed `quantity` | `direction`, `position_id`, average entry, unrealized PnL, snapshot scope |
| `equity_points` / account + time + revision | `event_ts`, `currency`, nullable `equity`, nullable `balance` | reported return, reporting method, drawdown, cash flow linkage |
| `pnl_points` / account/instrument + interval + revision | `start_ts`, `end_ts`, `currency`, `value`, `basis` realized/unrealized/total | fee inclusion, funding inclusion, source return basis |
| `cash_flows` / source movement ID | `event_ts`, signed `amount`, `currency`, `kind` deposit/withdrawal/dividend/funding/fee/other | instrument ID and linked event |

An execution with missing quantity/price remains a raw observation or a
lower-information event, not a valid row in `execution_events`. Never fill
missing execution values with zero to pass validation. Round trips may be
converted to entry/exit deltas only if quantity, lot semantics, times and
completeness justify it; derived rows cite their parent and derivation version.
Reported PnL is not overwritten by calculated PnL.

`InstrumentSpec` (effective-dated): `instrument_id`, venue/broker, source
symbol aliases, asset class, base/quote/settlement currency, `price_tick`,
`quantity_unit`, `quantity_step_units`, `min_quantity_units`,
`contract_multiplier`, `payoff_type` (`linear`, `inverse`, `option`, `unknown`),
calendar/timezone, expiry?, roll mapping?, shorting capability, corporate-action
policy, provenance refs. Decimal fields are strings in JSON.
Canonical `*_units` are integer multiples of `quantity_unit`; initially it
must equal one native share/contract/unit. Later fractional support changes
instrument scale explicitly, not the Int64 output type. A lot is not a unit:
convert using a verified lot-size mapping or block absolute sizing.

## 6. Market bars, labels, and dataset manifest

`bars` key `(instrument_id, open_ts, timeframe)`:
`open_ts`, `close_ts`, `available_ts`, `open`, `high`, `low`, `close`,
nullable `volume`, `timeframe`, `market_source_id`, `source_type`, `is_final`,
`adjustment_policy`, `evidence_id`. Price transforms use finite Float64.
Require open < close time, OHLC consistency, sorted unique keys, final bars,
explicit volume units, and no silent duplicate/revised bar selection.
`available_ts` cannot precede `close_ts` for final bars. Historical availability
estimated from close plus assumed delay must be labeled an assumption, not
confused with download time or claimed observed publication.

`observed_positions` key `(strategy_id, instrument_id, label_ts)`:
nullable `quantity_units`, nullable `direction`, `position_known`,
`direction_known`, `known_interval_id?`, `evidence_refs`, `derivation_version`,
`uncertainty_ns`. Integer conversion must be exact. A snapshot establishes
one point unless the source guarantees continuity; unknown intervals remain
unknown. Hedged books also retain gross long/short leg tables; net zero alone
cannot establish no exposure.

`DatasetManifest`: ID, schema version, raw evidence IDs, table artifact refs,
source strategy/account identities, source types, instrument-spec refs,
requested/actual windows, timezones and mapping versions, calendar ref,
market provider/license refs, row counts, missing-field counts, duplicate and
revision handling, coverage intervals/masks, known-start state, assumptions,
normalizer version, content digest. Separate complete executions from a
closed-trades-only export that omits positions crossing the window boundaries.

## 7. StrategySpec and generated positions

`StrategySpec` required fields: schema version, `strategy_id`, `family`,
`family_version`, `instrument_ids`, `timeframe`, `parameters`, `sizing`,
`execution_policy`, `warmup_bars`, `evidence_refs`, `hypothesis`, `limitations`.
`parameters` is a closed discriminated union by family, not free-form Python.
Family `sma_regime`: `{lookback:int>=2, band_bps:float>=0, allow_short:bool}`.
Family `channel_breakout`: `{lookback:int>=2, exit_lookback:int>=1, allow_short:bool}`.
Family `zscore_reversion`: `{lookback:int>=2, entry_z:float>0, exit_z:float>=0}`
with exit_z < entry_z. Additional families need versioned kernels and checks.

Initial sizing: `{mode:"fixed_units", units:positive int}`. Later sizing
variants must state prior-equity/volatility inputs and lot rounding semantics.
Execution policy initially `{decision:"closed_bar", fill:"next_open",
latency_ns:nonnegative int, shorting:"instrument_policy"}`. Parameters cannot
change the evaluation split or data-selection policy.

Public trusted model entry point:

```python
def generate_positions(
    bars: pl.LazyFrame,
    *,
    spec: StrategySpec,
    context: ModelContext,
) -> pl.LazyFrame:
    ...
```

The signature is a planned interface, not an implementation stub to ship.
`ModelContext` includes immutable instrument-spec refs, trading schedule,
requested output window, permitted data refs, as-of cutoff, and initial state.
It contains no clock, network client, LLM handle, observed target labels, or
unrestricted filesystem access. Required schedule identifies the next
tradable open even when the input ends before that bar.

`generated_positions` columns, all non-null:
`strategy_id:String`, `instrument_id:String`, `decision_ts:Datetime(ns,UTC)`,
`effective_ts:Datetime(ns,UTC)`, `target_units:Int64`, `signal_state:Int8`,
`reason_code:String`, `model_version:String`.
Unique key `(strategy_id,instrument_id,decision_ts)`, ascending per instrument.
Decision timestamps must increase strictly per instrument. If late batch
availability collapses several source bars to the same decision instant or
reorders them, reject the segment with `out_of_order_availability` until an
explicit versioned late-data decision policy is supplied.
After warmup, emit every valid requested decision point, including flat and
unchanged targets. `signal_state` equals sign(target_units) for executable
sized models. `target_units` is an absolute desired net position, not a trade
delta. Delta calculation belongs to replay. Direction-only reconstruction
uses an explicitly declared research sizing policy (e.g. one unit) and cannot
claim recovered absolute size. Invalid/missing bar gaps fail the requested
segment rather than manufacturing zero targets.

Decision/effective timing, equality at session boundaries, model state and
exact examples are normative in [04](04-model-recovery-and-positions.md).

## 8. Fit, evaluation, bundles, and run metadata

`SplitManifest`: dataset hashes, resolved universe, exact train/validation/test
intervals, eligible masks, purge/embargo settings, maximum feature lookback,
label-dependency horizon, disclosure of warmup carry-in, creation before
trial zero. Preprocessing fitted only on training data. Test labels are not
included in hypothesis prompts or fitting inputs.

`FitResult`: candidate/spec hash, split hash, parameters, objective definition,
training/validation metrics, seed, trial index/count, search bounds,
constraints, elapsed resources, code/dependency versions, diagnostics,
validation-selected rank. This rank is frozen before test evaluation.

`EvaluationReport`: candidate and split refs, evaluated window, claim,
metric entries `{name,value?,numerator?,denominator?,status,reason?}` where
status `computed`, `insufficient_support`, or `not_applicable`; baseline
results, timing/price tolerances, support and coverage counts, simulated
execution/cost assumptions, `decision` pass/fail/insufficient_evidence,
failed gates, equivalence-set/uncertainty notes, evidence refs. A missing
required metric is never a pass. Output test results for the frozen shortlist
without re-ranking or refitting from test outcomes.

`ModelBundle` directory contains `manifest.json`, `strategy_spec.json`,
`fit_result.json`, `evaluation_report.json`, `dataset_manifest.json`,
`split_manifest.json`, `instrument_specs.json`, `model.py`, `positions.parquet`,
`report.md`, and a dependency/runtime lock sufficient for offline replay.
Market/evidence artifacts are included only if licenses permit; otherwise
include hashes, provider acquisition instructions and allowed local references.
A **self-contained** replay claim requires actual lawful fixture/input bytes,
not just links. `model.py` uses the trusted spec interpreter or trusted
exported expressions, not an LLM call; manifest declares which runtime is
needed. All member hashes and provenance are listed; no credentials.

No-model bundles contain the request, evidence/dataset/split refs if produced,
trial summaries, a report, terminal outcome and missing/failed gates; no
misleading promoted `model.py` or `positions.parquet`. Candidate research
artifacts may remain in the run store marked unpromoted.

`RunManifest`: run ID, parent run?, request/hash, lifecycle fields from 01,
stage attempts, immutable artifact refs, budget limits/consumption, code and
schema versions, timestamps, user-action records, terminal summary. Catalog
SQLite tables: `runs`, `stage_attempts`, `artifacts`, `run_artifacts`,
`source_candidates`, `access_probes`, `model_candidates`, `operations`.
Keep large table contents in artifacts; add actual SQL migrations when code
exists. SQLite concurrency scope is one local writer; distributed execution
is not implied by this schema.
