# 07 — Current implementation: alpha reverse engineering and browser skills

This document supersedes the transport, installation, and delivery choices
in baseline plans 00–06. Those documents remain research/design references,
not a claim that every proposed command or future market engine exists.
The product means **reverse engineering trading alphas**, including converting
explicit, licensed trading rules into reproducible Python/Polars models.

## Decisions

1. **Skills + a real CLI, not a second agent harness.** Any agent with shell
   access can load the repository's skills and execute `uv run reta`. The
   host supplies language-model reasoning, discovery and hypothesis proposals.
   Numerical fitting, causal generation, evidence and model exports live in
   Python. No RETA-specific MCP server is required. An agent may also use REA's
   existing MCP over stdio; Make exposes an explicit reviewed setup target.
2. **Actual implementation outputs go under `output/`.** Each reverse/conversion
   run publishes a new directory atomically: source/spec/assessment/evaluation,
   Python model, requirements, canonical input and generated position artifacts,
   and a manifest with hashes. No overwrite of prior runs. A failed inference
   publishes a no-model report, not an invented model. Conversion and reverse
   engineering have distinct provenance and validation labels.
3. **BrowserSkill is the preferred existing-browser route.** Its CLI and
   extension act in an Agent Window with the browser's current authenticated
   profile, and explicitly borrowed tabs are returned. It does not need a
   copied password database or an exposed remote-debugging listener.
   Installation and extension pairing are separate capabilities.
4. **Playwright is the deterministic reference-script route.** It supports an
   isolated persistent project profile, programmatic login using environment
   secrets, bounded HTML-table collection, and explicit CDP attachment to an
   authorized browser. CDP mode creates/closes only a task-owned tab and never
   closes the attached browser or navigates existing user tabs.
5. **Hermes integration is skill-level.** Existing Hermes browser tools or
   BrowserSkill can acquire data; their export is imported into the same alpha
   workflow. RETA does not import Hermes as a Python dependency or copy the
   user's real browser profile. Hermes real-profile snapshot behavior is
   documented as an optional upstream feature, not silently enabled.

## Evidence behind the browser choice

- [BrowserSkill README](https://github.com/Tencent/BrowserSkill) and
  [agent installation](https://github.com/Tencent/BrowserSkill/blob/main/AGENT_INSTALL.md):
  CLI + extension + installed skill; explicit browser/session selection,
  visible Agent Window and task cleanup; doctor alone is not a successful task.
- [BrowserSkill extraction](https://github.com/Tencent/BrowserSkill/blob/main/docs/structured-extraction.md):
  extraction reads loaded DOM only; pagination is separate; dataset completeness
  is never asserted by a loaded table alone. Retain its coverage and sidecars.
- [Hermes browser guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/browser):
  CDP attachment and real-profile snapshots are separate from its default
  packaged browser. BrowserSkill sharing does not require either one.
- [REA setup](https://github.com/morluto/rea/blob/main/docs/installation.md):
  `setup --client ... --dry-run` previews registrations; setup is separate from
  npm installation and may change personal harness configuration. Do not
  install native analysis engines for trading evidence by default.

## Implemented public workflow contract

`reta demo` creates a deterministic redistributable research dataset and runs
real model fitting; it is explicitly synthetic, never marketplace evidence.
`reta reverse --request FILE` reads a bounded research request with bars and
observations, freezes chronological splits, evaluates a finite allowed model
grid, and emits a passing-model or no-model bundle. Evidence can be positions,
signals, executions, round trips or PnL/equity; lower-identifiability modalities
must not claim recovered absolute positions. Explicit known coverage, initial
position and quantity semantics are required where necessary.

`reta convert --spec FILE --bars FILE` converts a typed explicit rule into a
trusted Python/Polars model and positions. It is a white-box conversion, not
a held-out behavioral reconstruction claim. Arbitrary proprietary script
execution and generic Pine/MQL/AFL parsing are not presumed capabilities.
An agent uses the conversion skill to translate authorized explicit rules
into supported typed specs, then validates them on independent observations.

`reta positions --bundle DIR --bars FILE` verifies the bundle and replays the
exported model. Inputs and output semantics remain causal close-to-next-open
absolute target positions, not broker orders. Family support is explicit:
SMA regime, previous-bar channel breakout, z-score reversion. Unsupported
families/payoffs/account modes return errors rather than proxy models.

`reta browser login --provider FILE` and `reta browser collect --provider FILE`
use reviewed JSON selector/origin configs. Login reads `RETA_<ID>_USERNAME`
and `RETA_<ID>_PASSWORD`, or their `_FILE` alternatives, inside the process.
No plaintext credentials in command arguments, prompts, logs, screenshots,
raw captures, shared-browser subprocess arguments, or generated models.
MFA/CAPTCHA/SSO/human consent pauses instead of bypassing protection.

`reta browser shared --provider FILE` uses BrowserSkill on an explicitly
selected browser instance, starts its own session, navigates only the approved
source URL, extracts the reviewed table, records loaded-DOM coverage, and
stops the session on success/failure. If the extension is absent/disconnected,
report that exact missing prerequisite. Existing sessions are preferred over
password injection into a real logged-in browser. Credential-based login is
restricted to the isolated Playwright profile.

`reta skills install --harness NAME` copies whole skills, references and scripts
to a documented harness skill directory without overwriting user content.
A custom destination supports other shell-capable harnesses. No assumptions
that a fresh harness/model has already been authenticated.

## Security and ownership

- `.env`, `.env.*` except `.env.example`, `.reta/`, `output/`, `.tools/`, storage
  state and local credential profiles are Git-ignored. Profiles use mode 0700;
  auth state/captures use mode 0600. No auth captures during credential filling.
- Provider configs contain origin allowlists, login/data URLs, explicit success
  selector, table/pagination selectors, limits and permission/source metadata.
  Redirects and page requests cannot widen authority. HTTP localhost is denied
  unless an explicit private-network option is supplied for controlled local
  development. Re-check every navigation/request, including redirects.
- CDP endpoints are explicitly supplied loopback-only endpoints; never expose
  debugging over `0.0.0.0`. Attaching is consent to a selected instance, not to
  closing its browser or using arbitrary existing tabs.
- Credentials are resolved only for the selected provider. Child BrowserSkill
  processes receive a scrubbed environment, not all provider passwords.
- Extract only the selected table and structured provenance; never dump entire
  authenticated HTML, cookie jars, localStorage, request headers or profile DBs.
- Skills are guidance, not an OS sandbox. The harness user remains responsible
  for authorized access. Generated models are trusted finite-template code,
  not execution of LLM-produced source.

## Verification and publication

Exercise a real synthetic alpha reconstruction and exported-module replay;
authenticated Playwright login/collection against a controlled local HTTP
fixture with a genuine cookie/session; CDP collection while an existing tab
survives; skill installation to a temporary harness directory; and actual
CLI behavior for unsupported/insufficient evidence. Test bounded pagination,
secret exclusion, causality, unknown intervals, no-model outcomes, and bundle
integrity. Marketplace credential/extension access remains externally gated;
a local fixture never proves access to Chợ Bot or another provider.

Make targets install the Python project, Playwright Chromium, a selected
harness, BrowserSkill and REA separately; setup targets register skills and
preview/apply REA MCP configuration deliberately. Existing global tools are
reused, not silently upgraded. Commit design, numerical engine, browser/security,
and skills/setup/docs in small logical commits; push the configured remote.
