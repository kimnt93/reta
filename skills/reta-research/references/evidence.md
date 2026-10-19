# Canonical evidence

Use UTC-aware timestamps. Bars require instrument_id, open_ts, close_ts,
available_ts, next_open_ts, open, high, low, close. next_open_ts is the known
next scheduled tradable opening, not the next observed row after a gap.
Only final bars are accepted. Use a real venue/contract mapping, not a proxy.

Positions: instrument_id, event_ts, target_units (absolute signed integer
native position), optional position_known. Signals can instead supply signed
direction (-1,0,1). Hidden sizes cannot validate absolute positions.
Executions: instrument_id, event_ts, side (buy/sell), positive integer
quantity; source event_id is strongly preferred for deduplication.
Round trips: instrument_id, entry_ts, exit_ts, direction (-1/1), quantity.
PnL/equity imports can document ambiguity but cannot produce unique positions.

A research request includes objective, bars, observations, observation_kind,
claim, source_type, source_url, permission, complete_history, initial_position
where known, account_mode, families/candidate_specs, sizing_units, max_trials,
max_lookback and evaluation. Read `examples/request.json` in the project and
`uv run reta reverse --help`. Contract definitions live in src/reta/contracts.py.

complete_history is an assertion of continuous coverage, not a convenience
flag. False uses point matching; true permits carrying the latest known state.
Explicit unknown observations break continuity. Execution reconstruction needs
a complete netting ledger and known initial position. No hidden interval is flat.

Use `reta import --input source.csv --mapping columns.json --output canonical.parquet`.
Mapping: {"columns":{"instrument_id":"Symbol","event_ts":"Time","target_units":"NetQty"},"timezone":"Asia/Ho_Chi_Minh"}.
Map source symbols to verified canonical instruments before merging with bars.
All raw source data, imports, browser profiles and outputs remain Git-ignored.
