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
