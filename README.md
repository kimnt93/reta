# RETA — Reverse Engineering Trading Alphas

A skills-first toolkit for reconstructing trading behavior and converting
explicit alpha rules into executable Python/Polars position generators.
Any shell-capable harness can use it: Codex, Claude, Hermes, omp, or another
agent that can read `AGENTS.md` and the bundled `SKILL.md` files.

The harness supplies reasoning and source discovery. RETA supplies real
browser/evidence scripts, deterministic fitting, held-out behavioral
validation and model bundles. No custom RETA MCP server or embedded model API
key is required. REA can be connected separately over **stdio MCP**.

## Install

Requires Python 3.12+, uv, Make. Node/npm are needed only for selected external
tools. Installs reuse existing harness tools rather than silently upgrading.

```sh
make install
make install-browser
make install-harness HARNESS=codex
make install-rea
make install-browser-skill
make install-skills HARNESS=codex
```

`make bootstrap HARNESS=codex` combines those targets. BrowserSkill/REA npm
binaries install under ignored `.tools/`; Make adds them to its own PATH.
For direct use after installation:

```sh
export PATH="$PWD/.tools/bin:$PWD/.tools/npm/node_modules/.bin:$PATH"
```

Codex and Claude installation uses their official npm packages. Hermes reuses
an installed CLI or runs its official non-interactive source installer, which
manages its own runtime/user launcher; RETA's Python environment is separate.
Authenticate the chosen harness/model using that harness's own setup.

### BrowserSkill and REA setup are separate

```sh
make setup-browser-skill HARNESS=codex
make rea-plan REA_CLIENT=codex
make setup-rea REA_CLIENT=codex
```

BrowserSkill also needs the user-installed
[Chrome extension](https://chromewebstore.google.com/detail/hhcmgoofomhgciiibhipgmgkgnoenaoi)
or [Edge extension](https://microsoftedge.microsoft.com/addons/detail/browserskill/emacgiaaaiojkkpkddmmdfhmokgmnikg).
Pair it locally, then `bsk doctor` and `bsk browsers --json`. A binary install
is not extension pairing or proof of a successful browser task. Never install
extensions into a user's personal profile silently.

REA setup previews/asks before changing personal harness configuration.
`make rea-plan` is read-only; `make setup-rea` is the deliberate interactive
registration step. Native reverse-engineering engines are not needed for
trading observations and are not installed by RETA's targets.

## Try actual alpha recovery

```sh
uv run reta demo
```

The demo creates deterministic **synthetic** bars/observations and runs the
real bounded inference/evaluation path. Output JSON names the resulting
`output/reversed-<id>/` directory. It is not marketplace evidence.

For authorized data, copy `examples/request.json` beside your canonical
bars.parquet and observations.parquet, edit the source/permission/coverage,
then run:

```sh
uv run reta reverse --request /absolute/research/request.json
uv run reta inspect --bundle output/reversed-<id>
uv run reta positions --bundle output/reversed-<id> \
  --bars output/reversed-<id>/bars.parquet --output output/replayed.parquet
```

A request's paths are relative to the request file. `complete_history` is a
coverage assertion: never set true to make missing labels disappear.
Executions require a known `initial_position` and complete netting ledger.
Positions/signals without continuous coverage are scored at exact observed
points. Hidden/unknown intervals remain unknown. PnL/equity-only evidence
produces an insufficient-evidence report, not fabricated trades.

Supported families: trailing SMA regime, previous-bar channel breakout,
z-score reversion. The initial engine fits one netting linear instrument per
request with integer native units; conversion can generate independent
per-instrument targets. No inverse/options valuation, hedged book engine,
unknown lot-size conversion, arbitrary script execution or broker orders.
Instrument/venue/contract mappings remain the researcher's responsibility.

The chronological split and common lookback are fixed before search.
Validation selects the winner; test data evaluates that frozen choice once.
Metrics include macro-F1, one-to-one transition matching, normalized size
error, coverage, support and constant-direction baselines. Thresholds and
minimum support are configurable in `evaluation` before research. Failing
candidates do not trigger weaker gates or an invented fallback model.

## Convert explicit licensed rules

Use the `reta-convert` skill to translate rules exactly into a supported
AlphaSpec. This is white-box conversion, not blind recovery.

```sh
uv run reta convert --spec examples/spec.json --bars /absolute/bars.parquet
python output/converted-<id>/model.py \
  --bars output/converted-<id>/bars.parquet --output output/standalone.parquet
```

The exported model requires only its pinned Polars dependency. It does not
call an LLM, browser, RETA service or remote data provider. Do not execute
submitted Pine/MQL/AFL/Python directly; unsupported rules need an explicit new
typed family and independent numerical examples, not a silent approximation.

## Evidence and output layout

Canonical bars: instrument_id, open_ts, close_ts, available_ts, next_open_ts,
open, high, low, close; final bars only, UTC ns times. `next_open_ts` is an
explicit scheduled opening, including exchange-session gaps. Missing expected
bars are errors. Features use only available trailing data; decisions become
effective no earlier than a later bar's opening. Targets include flat and
unchanged decisions after warmup, not just trade changes.

Observations: positions/signals use instrument_id, event_ts, target_units or
direction; executions use event_ts, side, quantity, preferably event_id;
round trips use entry_ts, exit_ts, direction and quantity. Explicit column/
timezone mapping avoids guessed provider semantics:

```sh
uv run reta import --input output/provider-export.csv \
  --mapping examples/columns.json --output output/observations.parquet
uv run reta schema --kind request
uv run reta schema --kind spec
uv run reta schema --kind provider
```

A passing reverse bundle contains model.py, spec.json, positions.parquet,
bars.parquet, original evidence, labels.parquet, portable request.json,
source-request.json, split.json, trials.json, evaluation.json,
requirements.txt, report.md and a hash manifest.
A conversion bundle is labeled conversion_only. A no-model bundle contains
evidence and diagnostics but no promoted model. Bundle directories publish
atomically and are never overwritten; replay checks artifact hashes.
The portable request references bundled inputs, so `reta reverse --request
output/reversed-<id>/request.json` can repeat research without the original
input directory.

Generated contents of `output/`, `.reta/`, `.tools/`, `.env` and provider data
are ignored by Git; only output/.gitkeep tracks the empty directory.
Files containing evidence/state are private local files. Do not redistribute
bundles unless the source license permits every included input.

## Provider login and browser collection

Copy `.env.example` to `.env`, set mode 0600 and configure only your provider.
For provider id `chobot`, use RETA_CHOBOT_USERNAME and RETA_CHOBOT_PASSWORD,
or each name with `_FILE`. Environment overrides `.env`; supplying both a
nonempty value and a secret-file reference is an error. Never put values in
prompts, command arguments, provider JSON or committed files.

Provider JSON contains reviewed origin/selector/permission metadata, not
credentials. See `examples/providers/README.md` and the provider JSON Schema.
Chợ Bot login fields were inspected, but authenticated export selectors and
free-history permissions have not been verified; no fake ready-made connector
is shipped. The executable authenticated fixture is `scripts/browser_smoke.py`.

### Isolated Playwright profile

```sh
uv run reta browser login --provider /absolute/provider.json --headed
uv run reta browser collect --provider /absolute/provider.json
```

The dedicated profile is `.reta/browser/<provider>/`, never the live default
Chrome profile. Login needs an explicit authenticated success selector.
MFA/CAPTCHA/SSO/consent requires human action; no bypass or stealth service.
Only the selected table is exported, never the login form, cookies, storage,
full authenticated HTML or network headers. Collection is row/page/byte bounded;
loaded-DOM exhaustion never proves complete historical account coverage.

### Share an already logged-in real browser

Preferred: BrowserSkill CLI + extension, explicitly selected browser instance.
It creates its own Agent Window/session and stops that session after collection.

```sh
bsk browsers --json
uv run reta browser shared --provider /absolute/provider.json \
  --browser YOUR_CONFIRMED_INSTANCE
```

The wrapper captures one loaded table and retains upstream coverage. For
pagination, use the upstream browser-skill instructions to inspect and export
additional authorized pages. No password is passed to bsk. Shared browser
sessions share cookies/account state; avoid parallel account switching.

Alternative: explicitly attach Playwright to an authorized **loopback** CDP
endpoint. This requires a browser already launched with remote debugging;
modern Chromium generally requires a dedicated non-default user-data dir.
Never expose debugging on 0.0.0.0.

```sh
uv run reta browser collect --provider /absolute/provider.json \
  --cdp-url http://127.0.0.1:9222 --consent-shared-browser
```

RETA opens/closes only its owned tab, leaving existing tabs and the attached
browser alive. Credential login is disabled in shared mode. Isolated owned
Playwright requests use origin/private-address checks; existing real-browser
extensions/service workers and BrowserSkill's browser authority are outside
RETA's isolation boundary. Sharing is explicit trust, not a security sandbox.

Hermes can load these skills and use its own `/browser connect` or existing
browser tools, then import the export. Its optional real-profile snapshots
are an upstream opt-in feature; RETA never enables them or copies profile DBs.
See the [official Hermes browser guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/browser).

## Agent skills and verification

Read `AGENTS.md`; skills live in `skills/reta-research`, `skills/reta-convert`
and `skills/reta-browser-data`, including references and runnable scripts.
`reta skills install --harness codex|claude|hermes|omp` installs whole packs
without overwriting changed user skills; `--destination` supports other hosts.
Installed reference scripts use `RETA_PROJECT_ROOT=/absolute/reta`.

```sh
make check
uv run python scripts/browser_smoke.py
make demo
```

The browser smoke exercises actual isolated login, bounded authenticated
collection and CDP attachment against a controlled local site. It does not
prove live marketplace login or extension pairing. Exit 0 means a completed
command; reverse returns 4 for insufficient evidence/no candidate and 3 for
human-action prerequisites. Invalid input/capabilities return 2.

Current design: `plans/07-skills-browser-and-alpha-implementation.md`.
Baseline plans retain broader source/market research, not unavailable APIs.

### Current verification and external prerequisites

`make check` passes 23 behavioral tests, formatting and lint. Actual Chromium
smokes exercised env/_FILE login, session reuse, pagination and CDP attachment
without closing an existing tab/browser. REA 6.7.0 completed a real stdio MCP
initialize/tools-list handshake; no personal MCP configuration was applied.
Installed skill scripts were invoked successfully from outside this checkout.

BrowserSkill 0.3.3 and its Codex skill are installed, but its doctor reports
zero connected browsers: extension installation/pairing is still a user step.
No live marketplace credentials were supplied. Chợ Bot authenticated history,
export selectors and permission are not verified. Restart the chosen harness
to discover newly installed skills, then supply only reviewed provider config
and local secrets. Full delivery evidence is in plan 07.

