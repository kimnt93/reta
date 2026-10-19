# 06 — Verification, risks, and delivery evidence

## 1. What this planning deliverable does and does not verify

The repository initially contained no application to run. These files specify
future behavior; they do not claim tests, connectors, models, or an MCP server
already exist. Plan verification must check local links, JSON examples,
contract consistency and the numerical worked examples. Implementation
verification below requires actual program execution, not just passing mocks.

Checks exercised for this planning change: eight Markdown documents, local
relative links, fenced JSON parsing, and a disposable Python 3.12/Polars 2.0.0
calculation of the worked SMA outputs, equality-to-flat, future-append
invariance, cumulative ledger positions and reversal/fee accounting.
Observed targets were `[2,-2,-2,2,2]`; ledger positions `[10,6,-2]`; realized
gross PnL 32 and final marked equity change 29. This validates the numerical
examples, not an implemented RETA engine or a marketplace connector.

## 2. Required end-to-end implementation scenarios

| ID | Scenario and input | Expected observed result |
| --- | --- | --- |
| A01 | Offline authorized netting ledger, known start, matching final bars, allowed synthetic family | Raw evidence -> normalized dataset -> fitted typed spec -> held-out passing report -> executable bundle -> exact replayed positions |
| A02 | Same inputs from a fresh process/workspace using the exported bundle | Identical ordered positions and split/spec hashes; metrics within declared tolerance; no LLM/network request |
| A03 | Request URL for an audited real profile with permitted free data and matching market input | Actual access/permission artifacts, measured coverage, genuine model or no-model conclusion; not a mocked web response |
| A04 | Real automatic mode with configured provider | Sanitized training-only dossier -> actual structured proposal -> deterministic fit/validation; provider identity/call counters retained |
| A05 | External MCP host, no embedded LLM credentials | Import/build/submit/fit/validate/export/generate succeeds through the same use cases as CLI; stdio remains valid protocol |
| A06 | Hidden quantities, claim absolute_positions | Dataset can retain lower-information observations; run ends insufficient_evidence for sizing, no promoted absolute-position model |
| A07 | PnL/equity-only source | Ambiguity/coverage report; no fabricated trade ledger or behavioral promotion |
| A08 | Adequate data but all candidate families fail locked gates | no_candidate_passed, rejected trials and failed metrics, no weakening of thresholds |
| A09 | Login redirect, paywall, CAPTCHA, private history and true empty complete ledger | Distinct statuses; never parse a login page as zero trades; no bypass/purchase |
| A10 | Network interruption/cancel/crash during bounded collection or fit | Previously completed artifacts remain valid; owned worker stops; partial coverage/counters persist; resume uses correct checkpoint |
| A11 | Altered raw record, instrument spec or parser version after prior fit | New artifact/dataset/attempt; dependent results invalidated, old run remains reproducible |
| A12 | Later input appended or future bar/target labels changed | Past generated targets and frozen training/validation fits do not change |
| A13 | Shorting/quantity-step/session/roll/account mode incompatible with engine | Typed unsupported-capability or invalid-spec result; no proxy market or silent rounding |
| A14 | Prompt injection in a source description/export | Content retained as untrusted data; cannot change policy, reveal secrets, execute arbitrary code or adjust split/gates |
| A15 | Delayed availability and several decisions mapping to same later open | Effective times obey later-bar schedule; replay takes latest eligible target once; missing future opening price stays pending |

A real-source outcome need not be a passing model. It must faithfully report
what evidence supports. A01 establishes a passing controlled reconstruction;
A03 establishes real acquisition and inference honesty. Both are required.

## 3. Targeted behavioral invariants

### Data and provenance

- UTC ns round trips; source timestamp precision/zone retained; ambiguous
  local timestamps fail mapping unless a documented resolution is supplied.
- Stable IDs and append-only revisions; identical-value distinct partial
  fills survive, overlapping copies of the same event do not double count.
- Raw evidence locators and access/permission refs survive every derived row.
- Delayed/hidden positions remain unknown; no missing-value-to-flat conversion.
- Provider, subscriber, live, paper, backtest and model-account observations
  cannot silently merge. Closed-trades-only histories preserve boundary gaps.
- Source pagination exhaustion and historical completeness remain distinct.
- No license-restricted input is redistributed merely to make replay easy.

### Numerical and evaluation

- Exact SMA and partial-close/reversal examples in document 04.
- Model features partition by instrument and use only available trailing data.
- Breakout references exclude current bar; state initialization is explicit.
- Every requested valid decision after warmup appears, including flat and
  unchanged targets. A missing bar fails the segment, not skipped execution.
- Delta versus absolute target is not confused; reversal quantity is correct.
- Train/validation/test split is frozen before search; label dependencies are
  purged; held-out targets never appear in the dossier or fitting input.
- Transition matching is one-to-one with fixed tolerance, empty support is
  insufficient, and a majority/flat baseline cannot pass on accuracy alone.
- All trials/candidates count toward the same persistent request budget.
- Fees, funding, multiplier, currencies and cash flows are explicit. Compare
  PnL only on a common basis; do not choose profitable intrabar ambiguity.

### Operational and security

- MCP/CLI errors and domain no-model outcomes are distinguishable.
- Stdout is protocol/JSON only; all progress/logging is stderr.
- Path traversal, symlink escape, private-address URLs, malicious redirects,
  oversized input, resource exhaustion, and secret-bearing export are rejected.
- Resource pagination cannot disclose arbitrary files or credential stores.
- Safe spec execution works without arbitrary Python. A subprocess/AST filter
  is not accepted as proof of code isolation if arbitrary code is enabled.

## 4. Test and smoke strategy for implementation

Use permanent deterministic tests for the uncertain consumer-visible boundaries
above. Numeric tests compare actual values/state transitions, not source code
or implementation wording. Use captured fixtures only when license/redaction
allows them, and state their capture date/source. Live-source tests are an
explicit opt-in suite, never a default suite that requires user sessions.

For each feature, launch the actual CLI or MCP server and exercise the changed
path. Unit tests alone do not establish working packaging, permissions, process
lifecycle, or host transport. Keep evidence from a fresh offline bundle replay.
A real provider smoke cannot be replaced by a mocked structured-output echo.

Planned verification commands once the application exists:

```text
uv sync --locked
uv run ruff format --check src tests
uv run ruff check src tests
uv run pycodestyle --max-line-length=79 src tests
uv run pytest
uv run reta --workspace .reta-smoke research --request examples/request.json --json
uv run reta --workspace .reta-smoke runs inspect --run RUN_ID --json
uv run reta --workspace .reta-smoke bundle export --run RUN_ID --output result/ --json
uv run reta --workspace .reta-replay positions generate --bundle result/ --bars examples/bars.parquet --context examples/context.json --output positions.parquet --json
```

`RUN_ID` is the value returned by the research command, not a hardcoded ID.
Host mode pauses for hypotheses: use `hypotheses submit` and resume the run
before exporting a passing bundle. The example request, hypotheses, bars and
context must be shipped as a complete mutually consistent fixture set during
implementation. Add a smoke driver that captures IDs and uses actual CLI/MCP
calls; do not pretend this command sketch already executes today.

MCP proof must start `uv run reta --workspace .reta-mcp mcp serve` and connect
an actual SDK/host client. Check tools/list, import/build/submit/fit/validate,
resource paging, operation progress, cancellation and bundle replay. Observe
structured responses and artifacts, not just a server that stays running.

## 5. Risk register and required response

| Risk | Observable symptom | Required response |
| --- | --- | --- |
| Non-identifiability | Several models fit behavior equally well | Preserve equivalent candidates, disclose disagreements, avoid original-code claim |
| Insufficient/hidden history | Unknown intervals, missing quantities, capped pages | Report precise coverage and missing prerequisites; no flat fills |
| Source access changes | Redirect/login/privacy/rate restrictions change | Re-audit versioned scope; stop unauthorized collection |
| Market-input mismatch | Triggers differ by broker/venue/adjustment | Verify mapping, compare sensitivity, block unjustified PnL claims |
| Temporal leakage | Future data changes old outputs/parameters | Enforce availability and frozen splits; reject contaminated experiment |
| Repeated test overfitting | Thresholds/families change after test | New held-out/forward period and experiment identity |
| Survivorship/selection bias | Only top/active providers sampled | Report discovery selection and coverage; do not generalize to all bots |
| Execution/model-account artifacts | Follower sizes or re-marked fills mistaken for provider rules | Preserve account role/provenance and revisions |
| Ill-defined quantity/contract | Lots treated as units; missing multiplier/expiry | Require verified InstrumentSpec or direction-only changed request |
| Economic-accounting error | Deposit or funding appears as alpha | Reconcile cash flows/costs/currencies on explicit basis |
| Untrusted pages/code | Requests to run helpers, leak tokens or alter policy | Treat as data; strict tool authority and safe spec interpreter |
| Unbounded agent loop | Repeated searching/prompts/fits without progress | Shared caps, stage checkpoints and explicit no-model/blocked outcome |
| Fragile generated environment | Bundle only works in original session | Runtime lock + fresh-process replay and lawful input bytes |
| Secret/license leakage | Cookies/keys/protected history in report/bundle | Redact before exposure, separate restricted local originals, enforce export policy |
| Unsupported global engine | JP/VN/futures/options data normalized but valued incorrectly | Capability gates and independent financial examples, no linear proxy fallback |

## 6. External prerequisites and safe defaults

These are not unanswered architecture questions. Use the chosen defaults until
new evidence requires a versioned change:

| Item | Safe default / action now | Needed to pass an external gate |
| --- | --- | --- |
| Harness brand | CLI + standard MCP, no host-specific dependency | One real host integration exercise |
| LLM vendor/model | Host mode works without credentials; provider port | User-supplied provider settings for automatic-mode smoke |
| First marketplace | Audit priority sources, select first approved adequate one | Actual permitted free profile/export, not an assistant's claim |
| Search backend | Registry + supplied URLs; optional configured search port | Real search access for open-ended discovery |
| Market bars | Authorized/synthetic local import | Correct matching venue/contract history and rights for real reconstruction |
| Japan-specific history | Explicit unresolved source-discovery item | Official/access-tested detailed free history |
| Missing private source logic | No original-code guarantee | Cannot be proven from finite observed behavior alone |
| Arbitrary generated Python | Disabled; trusted spec/template models satisfy product | Enforced sandbox only if this extra capability is requested |
| Storage/deployment | Local files + SQLite, one user/writer | Measured multi-user/distributed need before new infrastructure |

## 7. Evidence to deliver with the implemented project

Include installation/runtime versions; exact CLI/MCP/scenario commands that
ran; request, split and model hashes; dataset coverage; access/license evidence;
baseline and candidate metrics with denominators; exported model/position
artifacts; fresh replay output; rejected/blocked cases; and unsupported
capabilities. Redact secrets without falsifying original artifact hashes.

A final report must distinguish **implemented**, **exercised**, **blocked by
external access**, and **not supported**. Do not say "done" because files
compile, a scaffold starts, a mock returns JSON, or a profitable backtest exists.
The user-visible behavior is request -> evidence -> tested model/no-model
result -> reproducible target positions where justified.
