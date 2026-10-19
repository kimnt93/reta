# Numerical inference discipline

Supported families: sma_regime, channel_breakout, zscore_reversion.
Use typed AlphaSpec, not arbitrary Python strings or a proprietary script.

The CLI freezes chronological training/validation/test boundaries before
search. It compares a fixed candidate grid, selects using validation only,
and evaluates the frozen winner on test once. Trials and failures are retained.
Do not repeatedly tune a request against the same test segment. New evidence
or a genuinely fresh forward period is required after test-guided changes.

Metrics include class-balanced direction macro-F1, one-to-one transition F1,
normalized size error, support and known-label coverage. Always-flat or a
constant direction cannot pass merely because direction accuracy is high.
Sparse points and hidden quantities cannot establish continuous/absolute paths.

Default sizing is a declared research policy until quantities support it.
For direction-only reconstruction, one-unit output is a runnable convention,
not evidence that the vendor traded one unit. No broker orders are emitted.

Candidate hypotheses should state family, feature lookback, timing, sizing,
supporting and contradicting evidence, and unavailable inputs. A complete
output is either a replayable passing bundle or a precise no-model report.
