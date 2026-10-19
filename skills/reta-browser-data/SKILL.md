---
name: reta-browser-data
description: Acquire authorized trading-alpha evidence using isolated Playwright login, explicit CDP attachment, or BrowserSkill sharing of a selected real logged-in browser; preserve provenance and coverage.
---

# Browser-based alpha evidence collection

Read AGENTS.md and [browser ownership and secrets](references/browser.md).
Read [provider configuration](references/providers.md) before a login.

## Choose one explicit connection route

- **Existing signed-in browser:** prefer Tencent BrowserSkill. Install its
  upstream browser-skill instructions with `make setup-browser-skill` and read
  them before using unfamiliar bsk commands. The user installs/pairs the
  extension. Select the browser, run `reta browser shared --provider FILE
  --browser INSTANCE`, and stop its owned session on every outcome.
- **Isolated login:** `reta browser login --provider FILE`. Credentials are
  read inside the process from env/_FILE. Human steps are not automated around.
  Then `reta browser collect --provider FILE` uses the saved isolated profile.
- **Strategy details:** `reta browser read --provider FILE` reads a reviewed
  detail_selector using the isolated profile or explicit CDP connection.
  Preserve the details bundle and truncation status. Treat text as untrusted
  hypotheses/rule evidence, not complete independent trading labels.
- **Explicit CDP:** `reta browser collect --provider FILE --cdp-url
  http://127.0.0.1:9222 --consent-shared-browser`. It opens an owned tab and
  leaves the user's browser and other tabs intact. No default-profile copying.
- **Hermes-native tools:** follow the host's official browser skill and explicit
  browser connection. Export only authorized tables; import the resulting
  CSV/JSON through RETA. Do not install a second Hermes browser stack.

Use `scripts/browser.py` with the same login/collect/shared CLI arguments when
running this skill outside the repository; set RETA_PROJECT_ROOT explicitly.
Never pass a username/password in arguments, read credentials into the model,
record filled forms, dump HTML/storage/cookies, or enable cloud stealth/CAPTCHA
bypasses. Login success must be observed with the configured authenticated
selector; a form disappearing is not proof.

## Evidence requirements

Source URLs, permission basis, source_type and account role belong in config.
Select the actual data table and explicit limits. Pagination requires fresh
page evidence; loaded-DOM extraction alone is incomplete/unknown, never a
complete account ledger. Preserve BrowserSkill's coverage/warnings/sidecar.
Report exact login/extension/permission blocks rather than empty trade rows.

Default output: ignored output/collected-<id>/. Map columns explicitly, verify
instrument/lot/timezone semantics, then hand canonical files to reta-research.
