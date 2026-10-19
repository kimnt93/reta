# 05 — Implementation backlog and agent handoff

## 1. Delivery ordering

Do not start with nineteen crawlers or an LLM loop. Establish a deterministic
offline vertical slice, then attach real evidence and automatic reasoning.
Each packet ends with exercised behavior, artifact evidence, and updated user
documentation. These are work assignments, not estimates or existing code.

| Packet | Deliverable | Depends on | Can run independently after prerequisites? |
| --- | --- | --- | --- |
| P00 | Package and authoritative typed contracts | These plans | First shared prerequisite |
| P01 | Artifact store, catalog, run/checkpoint/budget lifecycle | P00 | Yes, alongside P02 |
| P02 | Authorized local import + canonical tables | P00 | Yes, alongside P01 |
| P03 | Instrument/market alignment + justified position labels | P01, P02 | Shared numerical prerequisite |
| P04 | Trusted specs, Python/Polars generation, replay | P03 | Yes, alongside source audits |
| P05 | Bounded fitting, locked evaluation, bundles | P04 | Core offline vertical gate |
| P06 | CLI and MCP adapters | P01–P05 contracts frozen | Transport work may start earlier; complete after P05 |
| P07 | Automatic research orchestration + LLM adapter | P05, P06 | Yes, alongside P08 |
| P08 | Real access audit + first online connector | P01–P03, P06 | Yes, alongside P07 |
| P09 | Priority source breadth + global discovery coverage | P08 | Connectors can be isolated by domain |
| P10 | Expanded quantities, account/market engines | P05, instrument contracts | Sequence dependent valuation capabilities |
| P11 | Portable replay, security hardening, complete acceptance | P06–P10 | Final delivery gate; checks accrue earlier |

Source audits can start once the AccessProbe contract exists; a failed online
audit does not block the offline engine. No packet may report a live-source
success using synthetic data. External-access blockers are recorded precisely
while reachable packets continue.

## 2. Shared handoff rules

- Integration owner freezes contracts and their JSON Schema versions before
  dependent agents edit callers. Interface changes migrate every caller;
  no compatibility aliases or parallel obsolete implementation.
- Agents receive the request, input artifact IDs, allowed files, contract
  version, expected output and acceptance scenario. They do not receive
  unrelated credentials or implicit permission from the parent prompt.
- One owner per shared module. Parallelize genuine independent source adapters
  or transport/numerical slices only after schemas/use cases are stable.
- Each packet returns: changed paths, public symbols, actual command/scenario
  output, artifact references, limitations, and remaining external blockers.
- Run integrated checks once after a coordinated edit wave; do not have
  sibling agents rewrite shared manifests or run competing formatters.
- Permanent tests target plausible behavior bugs, not class existence,
  forwarded argument equality, source text, or incidental wording.

## 3. Work packets

### P00 — Package and contracts

**Own:** `pyproject.toml`, initial `src/reta/domain/`, interface schema models,
`schemas/`, synthetic fixtures in `examples/`, project setup documentation.

**Implement:** Python 3.12 + uv/hatchling, one console entry point, exactly
pinned supported Polars/MCP dependencies at this implementation point,
Pydantic edge schemas, frozen internal values, lint/type/test configuration.
Translate document 02 into one typed source of truth. Generate schemas and
validate versioning, ns timestamp round trips and decimal-scale rules.
Create legally redistributable synthetic inputs with explicit source type.
Do not copy unused infrastructure adapters from a generic service template.

**Acceptance:** an example request is parsed; invalid fractions, mode/budget
incompatibility, unknown fields, missing source identity and incompatible
claim dimensions are rejected by exact error codes. Round-trip a nanosecond
UTC timestamp without truncation; preserve a non-integer raw quantity without
pretending the initial integer engine can execute it. Resolve a typed source
record and emit schema artifacts from the same model definitions.

**Handoff:** package import/CLI boot command, contract symbols, schema versions,
fixture generation rules and tested dependency pins. No network prerequisites.

### P01 — Evidence/artifact store and run lifecycle

**Own:** `adapters/storage/`, run/budget/stage application services and local
catalog migrations. Consume P00 contracts; do not change their semantics.

**Implement:** SHA-256 content-addressed storage, transactional SQLite catalog,
atomic staging publication, artifact verification, source/revision links,
read pagination, run state/outcomes, per-stage input fingerprints, owned
operation workers, cancellation, persisted shared budget charging. Restrict
allowed roots and redact secret-bearing metadata. Keep source timestamps
separate from artifact creation time.

**Acceptance:** interrupted stage leaves no published partial artifact;
identical completed stage inputs resume without refetching; changed input
creates a new attempt and invalidates downstream results; conflicting source
versions remain readable. Two owners cannot mutate the same run concurrently.
Cancellation stops owned work and retains earlier evidence. Resume cannot
reset consumed bytes/pages/trials. Tampered artifact content fails hash check.

**Handoff:** store/repository protocols, operation lifecycle and real crash/
resume exercise output. Document local single-writer limit.

### P02 — Local evidence import and normalization

**Own:** `adapters/sources/imports/`, canonical mapping/normalization in `data/`,
ImportManifest schemas and fixtures, with P00/P01 interfaces.

**Implement:** CSV/JSON/Parquet input; explicit columns/timezone/precision/
units/currencies/provenance/completeness/permission; source row locators,
required-column diagnostics, invalid-row quarantine, exact identity/revision
rules. Accept every observation modality in document 02 even if later
assessment cannot recover a model from it. Keep canonical execution events
separate from round trips, signals, snapshots and PnL.

**Acceptance:** partial fills with identical values and distinct IDs survive;
repeated pages/rows of the same source record do not double exposure;
missing quantity is not zero; ambiguous local time or lot size blocks that
mapping; invalid data reduces declared coverage; source live/paper/backtest/
model-account classes survive import. PnL-only import succeeds as data without
claiming behavior is identifiable.

**Handoff:** complete import examples for executions, round trips, signals,
snapshots and equity/PnL; normalized Parquet with raw-evidence references.

### P03 — Instrument mapping, market data and labels

**Own:** instrument/calendar adapters, `data/alignment.py`, label reconstruction
and evidence sufficiency assessment. Implement pure rules with explicit
inputs; no source calls from numerical code.

**Implement:** effective-dated aliases/specs; one continuous linear-instrument
calendar and one exchange-session fixture; market export importer, final-bar
checks, availability-time joins, known-start quantity accumulation, interval
masks, partial-close/reversal semantics, contradictory snapshot diagnostics.
Admit or reject each requested claim by available modalities and units.

**Acceptance:** exact `[10,6,-2]` ledger from document 04; unknown initial state
and missing intervals remain unknown; subscriber records cannot merge into
provider state; final-only bars and backward availability joins reject leakage;
missing expected bars do not become a long artificial holding period;
boundary-crossing positions remain accounted for. A PnL-only absolute-position
request reaches `insufficient_evidence`, not a fabricated position table.

**Handoff:** dataset/assessment artifacts and explicit label/time masks ready
for fitting. A known-start, one-instrument offline dataset is now usable.

### P04 — Trusted model execution and causal positions

**Own:** `models/`, trusted execution worker, replay engine in `evaluation/`,
trusted Python exporter. Use exact contract from 02 and semantics from 04.

**Implement:** SMA regime, previous-bar channel breakout, z-score reversion;
fixed-unit sizing; model/context validation; sorted partitioned Polars
features; state initialization; decision/effective time; complete long-form
positions after warmup; netting replay, pending targets, declared slippage/
fees, linear PnL. Executable models require no LLM/network call.

**Acceptance:** exact five-row SMA example; equality outputs flat;
future mutation leaves old decisions unchanged; per-instrument windows do not
mix; later-bar opening never current open; delayed inputs defer execution;
colliding effective-time targets use latest decision; missing final open is
pending, not an invented fill; fees/reversal accounting produces 29 equity
change in the document 04 fixture. Model context cannot read labels.

**Handoff:** invoke model generation and replay from a small real command or
throwaway script and observe exact outputs. Use a generated exported module,
not only direct calls to a test helper.

### P05 — Fit, held-out evaluation and result bundles

**Own:** search/split/metric/promotion services and bundle exporter. Consume
P04 kernels; do not introduce a second simulator for evaluation.

**Implement:** pre-search SplitManifest; deterministic bounded search;
training-only dossier/preprocessing; validation shortlist freeze; one-time
test; per-class metrics and one-to-one transition matching; quantity/PnL
claim gates; independent deployable baselines; insufficient-support handling;
versioned passing and no-model bundles, dependency/runtime metadata.

**Acceptance:** synthetic generator produces a ledger from a known allowed
family; hide its parameters from inference; split/fit/recover a model whose
held-out outputs meet predeclared gates. A counterexample from an unsupported
family returns no-candidate rather than relaxing rules. Always-flat fails
transition support even at high raw accuracy. Mutating test targets cannot
change fitted parameters or validation rank. All trials are counted.
Export and replay in a fresh workspace without an LLM/web call.

**Handoff:** **offline vertical gate**: authorized/synthetic import -> canonical
labels -> fitted spec -> held-out report -> exported Python -> positions.
Evidence includes full commands, bundle manifest and matching replay digest.

### P06 — Agent-friendly CLI and MCP

**Own:** `interfaces/cli/`, `interfaces/mcp/`, transport composition, MCP host
workflow documentation/skill. Numerical/business rules stay in application.

**Implement:** every command/tool in document 01, typed errors/outcomes,
resource summaries/pages, stderr progress, MCP structured output, operation
references, cancel/inspect/resume. Make direct low-level operations usable
without embedded LLM credentials. Scope imports/exports/resource reads.

**Acceptance:** launch actual CLI and MCP stdio processes. A host client calls
import/build/submit/fit/validate/export/generate, observes actual artifacts,
and retrieves a bounded evidence page. CLI and MCP produce the same artifact
identity for identical semantic inputs. MCP stdout contains only protocol
frames. Cancel a running owned fit, then resume checkpoints without duplicate
trials. Inspecting an insufficient-evidence run is not a transport failure.

**Handoff:** real host configuration example using `uv run reta ... mcp serve`,
validated tool input/output schemas, CLI exit behavior, copy-paste replay
instructions and source-policy guidance for other agents.

### P07 — Bounded automatic research workflow

**Own:** application stage orchestrator and `adapters/llm/`; request execution
uses the same public services as P06. Do not add an unconstrained shell agent.

**Implement:** natural-language objective plus structured constraints,
training-only dossier/prompt templates, one configured provider's typed
StrategySpec generation, candidate rejection diagnostics, accounting and
finite loop limits. Source policy, trial cap, split and promotion remain
outside model authority. Host mode pauses for submitted hypotheses; automatic
mode reports missing provider config without disabling deterministic tools.

**Acceptance:** actual configured provider proposes a schema-valid hypothesis
from a training-only dossier; deterministic fitting/validation/bundle replay
completes. If provider credentials are unavailable, validate deterministic
workflow and typed missing-provider path, and mark the real-provider gate
blocked—not demonstrated by a mock response. A malicious strategy description
cannot change allowed origins, reveal secrets, run code or change thresholds.
Budget exhaustion stops new calls/trials and preserves the run report.

**Handoff:** sanitized provider/model/template IDs and evidence of exercised
path; do not retain API keys or sensitive source account content in prompts.

### P08 — Audit and first online evidence connector

**Own:** source registry/discovery/access workflow and one approved connector;
use document 03 audit steps. Audit the five priority families before choosing
the first source. This selection is evidence-driven, not fixed by the plans.

**Implement:** guest/free-login separation, permission review, safe retrieval,
raw snapshots, field semantics, paginated window collection, rate/byte/page
caps, revision handling and market-data pairing. User handles login through
an isolated local profile; the harness sees only an opaque reference.

**Acceptance:** real permitted no-payment data produces AccessProbe, raw
history, DatasetManifest, market alignment, numerical assessment and a
replayable model or honest no-model outcome. Demonstrate at least two pages
or an explicitly single-page complete export; record exactly why coverage
is complete/partial/unknown. Login redirect, hidden history and paid-only
access are distinct from an empty complete history. Repeated capture detects
revision or proves unchanged content for the measured window.

**Handoff:** **online vertical gate**: request/URL -> audit -> evidence ->
assessment -> model/no-model report. Provide reproducible access steps and
license/terms references, not credentials or invented unpublished endpoints.

### P09 — Priority sources and worldwide discovery

**Own:** independent source adapters under versioned capability contracts;
registry/localization/search queries and per-market discovery report.

**Implement:** the remaining audited priority families cTrader Copy, MQL5
Signals, Collective2, Bybit, Chợ Bot. If automated collection is not permitted,
implement the permitted export path and record the unsupported automatic
capability rather than bypassing controls. Audit every other candidate in
document 03 and explicitly research Japan-specific free detailed histories.
Track forex/CFD, crypto, US, JP, VN and commodity coverage separately.

**Acceptance:** source report accounts for all nineteen candidates plus the
Japan-specific search result, with dated evidence and real access statuses.
Every approved adapter is exercised on a real permitted profile/export and
captured licensed fixtures; blocked domains do not expose placeholder success
methods. A storefront -> linked monitor trace retains both source identities.
Discovery exclusions and active-provider/top-performance sampling bias are
reported. No claim that all nineteen platforms support free historical trades.

**Handoff:** capability matrix, acquired dataset counts/depth/field-completeness
measurements and blocked-source evidence. Broader sampling follows actual
access grants, not an arbitrary ten-strategies-per-platform promise.

### P10 — Broader quantity, account and market semantics

**Own:** versioned instrument/payoff/calendars, sizing, account reconstruction
and valuation capabilities. Keep the initial linear engine operational.

**Implement in order:** (a) exact fractional quantities via verified integer
quantum; (b) fixed-notional/volatility sizing with causal prior inputs;
(c) exchange sessions/corporate actions and actual dated futures/roll events;
(d) currency conversion and funding/cash-flow accounting;
(e) hedged legs with gross/net targets and compatible output schema version.
Inverse contracts/options valuation require explicit payoff metadata and
independent reference examples before support; otherwise return unsupported
capability. Do not represent a non-linear instrument with a linear proxy.

**Acceptance:** fractional lot conversions conserve native exposure; a
multi-leg net-zero hedged book retains gross risk; next session respects
calendar/timezone; split/dividend adjustments do not create fictional returns;
roll closes one actual contract and opens another; causal FX/funding tests
reconcile PnL. Multi-instrument models cannot borrow future data or sizing
state from another instrument. New public output versions migrate callers.

**Handoff:** explicit supported/unsupported capability table per market and
payoff/account mode; independent financial examples and exercised position
outputs. Source breadth alone is not evidence of valuation support.

### P11 — Reproducibility, security and final acceptance

**Own:** integrated acceptance scripts, portable bundle/replay behavior,
operator/agent usage docs, license/redaction checks and final evidence report.

**Implement:** all scenarios in document 06; fresh-process offline replay;
source and request injection defenses; root/origin controls; resource limits;
checks for secrets in MCP/evidence/bundles. Exported model remains trusted
spec/template execution. Arbitrary generated-Python execution is not necessary
to satisfy the product; if added, require an actually enforced sandbox and
negative escape scenarios, or disable that capability explicitly.

**Acceptance:** every applicable delivery gate in 06 has observed command/
artifact evidence. Independent agent can execute documented request -> result
and bundle -> positions without conversation history. External-access/provider
blocks name exactly what remains unavailable; no fabricated verification or
unpromoted model is presented as success. Docs distinguish source-read
permissions from redistribution rights and fidelity from profitability.

**Handoff:** runnable installation/CLI/MCP/replay instructions, support matrix,
all exercised verification, known external prerequisites and no stale shims.

## 4. Definition of implementation completion

- **Core completion:** P00–P08 plus P11 checks applicable to that scope; offline,
  host-driven, automatic, and at least one real-source workflow are exercised.
- **Broader project completion:** P09–P10 capabilities and source audits are
  exercised or explicitly externally blocked, with no unsupported claims.
- Synthetic fixtures prove engine behavior only. Real marketplace permission,
  real LLM integration, and free-data availability each require their own
  evidence. A blocked external gate is not relabeled complete.

These definitions guide future implementation work; this current change is
the planning deliverable, not an assertion that any packet has been built.
