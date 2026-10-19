# 00 — Project analysis and product decisions

## 1. What was actually requested

The current request asks for analysis and detailed plans under `plans/`,
readable by other AI agents. The project workspace was empty when inspected:
there is no existing code, framework, database, or test suite to preserve.
All package layouts, interfaces, thresholds, and milestones below are design
decisions, not claims about implemented functionality.

The [shared conversation](https://chatgpt.com/share/6ad5bd3c-013c-83ec-a2fe-b65ec73add03)
contains six messages. The decisive user message is the fifth: reverse
engineer a trading model from signals, positions, trades, and PnL; discover
bot/strategy marketplaces exposing historical behavior; include Vietnam,
forex, crypto, US, Japan, and commodities; allow login but require free
access. It names Chợ Bot, cTrader bots, TradingView scripts, and MQL5, and
cites [morluto/rea](https://github.com/morluto/rea) as inspiration.

The current request adds the product shape: an agent harness receives a
request, finds and reads evidence, and returns models, potentially written
in Python/Polars, that generate positions. Therefore this is **not** a
marketplace to sell bots, a generic chatbot, an indicator directory, or a
live copy-trading service.

## 2. Proposed product definition

**RETA is an evidence-first toolkit for reconstructing plausible trading
behavior and exporting independently replayable position-generating models.**

A successful research result contains:

1. The original request, resolved instruments, time horizon, and access limits.
2. A source/access audit, immutable raw evidence, and explicit coverage gaps.
3. Normalized observations and aligned point-in-time market data.
4. Candidate model specifications, fitted parameters, and rejected hypotheses.
5. Held-out behavioral-fidelity results, baselines, and uncertainty.
6. For candidates that pass the requested gates: a versioned model bundle,
   Python/Polars entry point, and target-position Parquet output.
7. For inadequate evidence or failed reconstruction: an honest report naming
   missing prerequisites or contradictions, without a promoted model.

An executable approximation is the target. Exact identification of a private
strategy is usually impossible from finite observations: different rules,
hidden inputs, execution effects, discretionary actions, and parameter sets
can produce the same trades. Matching PnL alone is especially ambiguous.

## 3. Reassessment of the previous answer

| Previous suggestion | Decision for this project | Reason |
| --- | --- | --- |
| Start with four platform collectors | Audit several; implement one verified connector first | Free listing access does not establish free historical exports |
| Rank platforms with numeric suitability scores | Remove those scores | They were subjective, not measured access or extraction results |
| Store each trade as one entry/exit row | Preserve observations and execution events first | Partial closes, reversals, revisions, and hedged books do not fit one round trip |
| Use LLMs to infer the model | LLM proposes typed hypotheses; deterministic code fits and validates | Language plausibility is not behavioral evidence |
| Prioritize profitable backtests | Prioritize held-out behavior reproduction | Profitable unrelated strategies do not solve reconstruction |
| Call platform history live fills | Preserve explicit provenance categories | Backtests, paper signals, model accounts, and subscriber fills differ |
| REA-style reverse engineering | Reuse evidence/tool workflow, not native-binary machinery | This target is trading behavior, not executables |

The REA [README](https://github.com/morluto/rea#how-rea-works) and
[evidence workflow](https://github.com/morluto/rea/blob/main/.agents/skills/reverse-engineer-anything/references/evidence-workflows.md)
were inspected. Useful principles: CLI/MCP share workflows; conclusions cite
retained evidence; missing coverage remains unknown; verification concerns a
finite declared specification. RETA should not fork REA or depend on Hopper,
Ghidra, Android bridges, or REA's TypeScript runtime.

## 4. Scope and boundaries

### Required capability progression

- Accept natural-language objectives plus explicit structured constraints.
- Discover candidate sources from URLs, platform names, or configured search.
- Audit access/permissions before collecting; free login can be user-assisted.
- Ingest signals, execution events, round trips, position snapshots, and
  equity/PnL series without pretending they have equal information content.
- Normalize instruments and time semantics; reconstruct only justified labels.
- Search simple model families and produce executable Python/Polars models.
- Evaluate held-out entry/exit/position/sizing fidelity where identifiable.
- Generate historical or new-bar target positions without contacting brokers.
- Expose the same operations through CLI and MCP to external coding agents.
- Offer a bounded automatic research workflow with an explicitly configured
  LLM provider; retain all intermediate artifacts for inspection/resumption.

### Initial executable engine boundary

One strategy, one linear instrument, one timeframe, netting account semantics,
and integer native units/contracts. Include a known-start-position fixture.
This is the first complete implementation slice, not the entire product.
Broader source discovery and schemas must exist without pretending advanced
engines already work. Fractional native quantities, hedged reconstruction,
multi-instrument allocation, FX conversion, exchange-session futures/rolls,
and non-linear valuation have explicit later packets in document 05.

US/JP/VN and commodity instruments remain discovery targets. Research may
return `unsupported_capability` for an unavailable valuation or position
engine. Never silently substitute BTC prices for VN30 futures or CFDs for
exchange-traded futures. Japan-specific free detailed-history access has not
been established by the discussion or this analysis.

### Not in scope

Broker order execution, capital custody, paid subscriptions, bypassing hidden
history or access controls, redistributing proprietary datasets, promises of
profitability, or claiming to recover the vendor's original source. Open
source script translation may be a declared white-box reference exercise;
it must not be reported as blind reverse engineering.

## 5. Technology choices

| Concern | Proposed choice | Boundary |
| --- | --- | --- |
| Runtime/package | Python 3.12, uv, hatchling, committed lockfile | Exact dependencies selected and pinned during P00 |
| Numerical pipeline | Polars LazyFrame, Parquet, optional NumPy kernels | No pandas or per-bar Python callbacks in vectorizable transforms |
| Typed contracts | Pydantic v2 at interfaces; frozen domain values | JSON Schema emitted from one source of truth |
| Run/catalog metadata | SQLite, standard-library adapter | Single local writer; large tables stay in Parquet |
| Artifact storage | Local immutable content-addressed files + JSON manifests | Portable bundles; storage port permits later object store |
| Harness transport | CLI JSON and official Python MCP SDK over stdio | Same application services; no HTTP server required |
| HTTP/browser | httpx for permitted HTTP; optional Playwright connector support | Browser capability absent unless installed and needed |
| LLM integration | Provider port plus one configured structured-output adapter | Host-driven operation needs no model API key |
| Model execution | Typed StrategySpec interpreter and trusted Python exporter | Untrusted code is never executed in the host process |
| Verification | pytest plus actual CLI/MCP replay scenarios | Test observable invariants, not implementation text |

Do not add Kafka, Redis, Celery, PostgreSQL, a vector database, GPU training,
a distributed agent scheduler, or a web UI to the initial design. Bounded
search and file/catalog queries do not require these systems. Reconsider
only with a concrete concurrency, durability, or retrieval requirement.

## 6. Readiness and remaining prerequisites

Ready now: implement schemas, storage, local import, replay, deterministic
model families, metrics, and CLI/MCP. No marketplace credentials are needed
for this work.

Needed for the first real-source demonstration: a permitted detailed history,
source timestamps/quantity semantics, suitable matching market data, and a
record of usage rights. Document 03 specifies access probes rather than
assuming those resources exist.

Needed for automatic LLM research: user-selected provider credentials and
model identifier, supplied outside requests/artifacts. Absence blocks only
automatic hypothesis generation, not host-driven deterministic workflows.

Needed for a strong reconstruction claim: adequate training/validation/test
coverage, comparable observed behavior, and predeclared thresholds. If these
are absent, ship an evidence report, not a promoted approximation.

## 7. Project-level acceptance

A user or external agent can give RETA a permitted source URL or local
history export, inspect exactly what was collected, run bounded inference,
and either replay a passing model to target positions or receive a precise
no-model outcome. A second agent can reproduce the result from the bundle
without the original web session or an LLM call. Full implementation gates
are in [05](05-implementation-backlog.md) and [06](06-verification-and-risks.md).
