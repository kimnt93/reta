# Provider configurations

Provider JSON is user-reviewed metadata, never a place for passwords. Print
the current full schema with `uv run reta schema --kind provider`.
The authenticated local browser smoke in `scripts/browser_smoke.py` generates
and exercises a complete real configuration for its controlled fixture.

For a live source, configure id, allowed_origins, data_url, table_selector,
permission, source_type and account_role. Authenticated sources additionally
need authenticated_selector. Programmatic login needs login_url,
username_selector, password_selector and submit_selector. Pagination requires
an inspected next_selector; limits are explicit.

For description-only evidence, use detail_selector instead of table_selector
and run `reta browser read --provider FILE`. The selector must target the
inspected strategy content, not body/html or a login form. Set
require_authentication=false for public descriptions. This captures bounded
visible text, not licensed source code or a complete trade ledger.

The environment example covers all inventory sites. Use these provider IDs:
ctrader (Copy/Store), mql5 (Signals/Market), collective2, myfxbook, fxblue,
bybit, okx, binance, bitget, chobot, darwinex, tradingview, etoro, tradetron,
zulutrade, signalstart, composer. An unlisted site can use any valid reviewed
ID. With no provider credentials configured, RETA uses the user-supplied
RETA_DEFAULT_USERNAME/PASSWORD pair or its _FILE references. Provider-specific
credentials win as a whole pair. No defaults are embedded, no accounts are
created, and credentials do not establish source collection permission.

## Public cTrader description examples (2026-10-19)

`ctrader-rsi2-details.json` and `ctrader-orb-details.json` select the inspected
Description sections of actual products 440 and 4336. Both were read with
the real CLI in isolated Chromium, and REA passively inspected both pages.

```sh
uv run reta browser read --provider examples/providers/ctrader-rsi2-details.json
uv run reta browser read --provider examples/providers/ctrader-orb-details.json
```

These examples collect public descriptions only. RSI/EMA and session/retest/
ATR management are outside RETA's three current model families. The displayed
rules leave exit parameters or filter details unspecified, and neither
description supplies independent position labels or matching bars. Their
intake result is no-model; no numerical recovery/backtest is claimed.

## Chợ Bot observations (2026-10-19)

Inspected https://chobot.vn/login in Chromium without submitting credentials:
login form action /login, method POST; username input #user (name user),
password input #pass (name pass), button[type='submit'] labeled ĐĂNG NHẬP.
A sampled /bot/<id>/orders route redirected to login as a guest.

Authenticated success markers, order-table selectors, current free access,
historical depth and collection permission are **not verified**. No fabricated
ready-to-run Chợ Bot config is shipped. Once authorized, inspect the actual
success/table controls and supply a reviewed config. Use
RETA_CHOBOT_USERNAME/PASSWORD or _FILE, never plaintext JSON/CLI credentials.

BrowserSkill needs a matching connected browser instance and extension;
installing the bsk binary alone does not connect your real browser. BrowserSkill
exports use stable c1/c2 keys: use its columns metadata to create an explicit
mapping before importing, and retain coverage/warnings.
