# RETA plans

**Current build specification:**
[07 — Skills, browser access and trading-alpha implementation](07-skills-browser-and-alpha-implementation.md)
and [08 — Vectorbt backtesting](08-vectorbt-backtesting.md).
Read them with the root `AGENTS.md` and `README.md` before implementing changes.

RETA means reverse engineering **trading alphas**: discover authorized
observations, formulate testable hypotheses, fit/evaluate behavior, and export
Python/Polars position-generating implementations. Explicit-rule conversion
is supported but labeled separately from blind reconstruction.

## Current decisions

- Skills plus a real CLI are the portable harness interface; any shell-capable
  harness can drive the workflow. No custom RETA MCP server is required.
- BrowserSkill shares an explicitly selected real logged-in browser through
  its extension; Playwright provides isolated credential login and explicit
  CDP attachment. Never silently copy a personal profile or dump cookies.
- Provider secrets come from environment variables or `_FILE` secret references.
- Reversed/converted models and research evidence go into ignored `output/`.
- Make installs the project, selected harness, browser tooling and REA through
  separate targets; registering REA MCP over stdio is an explicit setup step.
- Numerical validation decides model promotion; the host agent supplies LLM
  reasoning. Missing evidence yields a no-model outcome, not fabricated alpha.
- Vectorbt backtests report economic performance separately from behavioral
  fidelity, with explicit costs, causal fills and independently funded
  held-out runs. Missing models never produce fabricated portfolios.

## Baseline research/design references

Documents 00–06 describe the original broader architecture and research
backlog. They are not an implemented-command catalog. Document 07 supersedes
conflicting transport, layout, installation and delivery assumptions.

| Reference | Subject |
| --- | --- |
| [00](00-project-analysis.md) | Original request, limitations and market scope |
| [01](01-architecture.md) | Evidence-first architecture and broader state-machine proposal |
| [02](02-data-contracts.md) | Detailed domain semantics and broader schema proposal |
| [03](03-source-discovery.md) | Nineteen source candidates and permission/free-access audits |
| [04](04-model-recovery-and-positions.md) | Identifiability, causality, numerical validation and model families |
| [05](05-implementation-backlog.md) | Broader source/market capability backlog |
| [06](06-verification-and-risks.md) | Security, fidelity and implementation acceptance scenarios |

The [shared discussion](https://chatgpt.com/share/6ad5bd3c-013c-83ec-a2fe-b65ec73add03)
and [REA](https://github.com/morluto/rea) remain the original inspiration.
Browser integration was reassessed from the official BrowserSkill and Hermes
references linked in document 07. Do not treat documented platform features
as proof that a given free profile exposes a complete authorized trade ledger.
