# RETA implementation plans

Status: design and implementation handoff; no application code exists yet.

RETA is the working project name for an agent-driven **trading-strategy
reverse-engineering toolkit**. It accepts a research request, discovers and
reads permitted trading evidence, constructs testable model hypotheses,
validates them numerically, and exports Python/Polars models that generate
target positions. It does not promise recovery of proprietary source code.

## Read in this order

| Document | Purpose |
| --- | --- |
| [00 — Project analysis](00-project-analysis.md) | User intent, source discussion, scope, decisions, limitations |
| [01 — Architecture](01-architecture.md) | Harness integration, use cases, state machine, module ownership |
| [02 — Data contracts](02-data-contracts.md) | Authoritative requests, evidence, datasets, specs, outputs |
| [03 — Source discovery](03-source-discovery.md) | Marketplace inventory, verified observations, access audit, collection |
| [04 — Model recovery and positions](04-model-recovery-and-positions.md) | Inference, fitting, validation, executable semantics, worked example |
| [05 — Implementation backlog](05-implementation-backlog.md) | Dependency-ordered agent work packets and completion gates |
| [06 — Verification and risks](06-verification-and-risks.md) | End-to-end scenarios, security, evidence, remaining prerequisites |

Read all eight documents before implementing a component. Document 02 owns
field names and types; 04 owns numerical semantics; 01 owns public command
and tool names; 05 owns implementation dependencies. An interface change
must update every affected document, consumer, and behavior check together.

## First implementation assignment

Start with work packets **P00–P03** in document 05: contracts, artifact/run
storage, local evidence ingestion, then causal labels and market alignment.
Next, complete deterministic model execution and fitting before adding an LLM
or a marketplace-specific crawler. Build the complete offline vertical path,
then prove the same workflow against one audited, permitted online source.

This ordering is not a reduction of the global discovery goal. It separates
an executable core from uncertain source access, so hidden marketplace
history does not prevent useful work with authorized user exports.

## Instructions to implementing agents

- Treat these files as a proposed build specification, not existing behavior.
- Keep observed evidence, derived data, and inferred hypotheses separate.
- Never invent histories, missing quantities, source permissions, or scores.
- A no-model conclusion is valid; a fabricated model is not.
- Deliver real CLI/MCP behavior and replayable artifacts, not just modules.
- Keep the project usable by external agent harnesses without requiring an
  embedded LLM provider. Automatic research is a separate configured mode.
- Do not add databases, queues, web dashboards, or broker execution before
  the requirements in these plans need them.
- Verify each completed packet using its observable acceptance scenarios.

## Design provenance

The [shared discussion](https://chatgpt.com/share/6ad5bd3c-013c-83ec-a2fe-b65ec73add03)
was read in full. Its final request explicitly concerns reverse engineering
from signals, positions, trades, and PnL across global markets, with free
access or free login. [REA](https://github.com/morluto/rea) supplies the
inspiration for evidence-first tools, not a trading-model implementation.
Research observations and direct source links are recorded in documents 00
and 03. Planning date: 2026-10-19.
