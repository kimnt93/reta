---
name: reta-convert
description: Convert authorized explicit trading alpha rules into typed Python/Polars position-generating models, with provenance, vectorbt backtesting and independent behavioral checks.
---

# Convert explicit trading rules

Read AGENTS.md and [conversion requirements](references/conversion.md).
Use this when the user provides licensed source/rules, not when inferring
unknown rules from behavior alone.

1. Identify source language, licensing, timeframe, instrument, indicators,
   execution timing, state, exits and quantity semantics.
2. Translate only when an exact supported AlphaSpec expresses the rule.
   Read `src/reta/contracts.py` and `src/reta/kernel.py`; do not approximate an
   unsupported rule silently. Add a properly verified family when necessary.
3. Preserve source attribution/license in the research record. Do not execute
   arbitrary submitted Pine, AFL, MQL or Python in the host process.
4. Write the spec and canonical bars. Run `python scripts/convert.py --spec
   /absolute/spec.json --bars /absolute/bars.parquet`, or `uv run reta convert`.
5. Inspect output/<converted-id>/model.py, spec.json, positions.parquet,
   evaluation.json, backtest.json, report.md and manifest.json. Conversion
   includes financial simulation, not blind recovery or held-out fidelity.
   Supply `--backtest-config FILE` for explicit capital/cost assumptions.
6. Independently compare against authorized reference positions using the
   research workflow before claiming equivalence. Include boundary examples
   for warmup, equality, partial exits, sessions and timing.
   Existing bundles can be simulated with `uv run reta backtest --bundle DIR
   --config FILE`; that command never changes the source bundle.

The portable exported model requires Polars, not an LLM, browser or RETA MCP.
