"""Owned-tab browser login and collection with explicit profile authority."""

import hashlib
import json
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import (
    BrowserContext,
    Page,
    Route,
    sync_playwright,
)
from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from reta.artifacts import bundle_directory, publish_manifest, write_json
from reta.browser.config import ProviderConfig, origin, public_url
from reta.browser.policy import NetworkPolicy, validate_cdp_endpoint
from reta.contracts import RetaError
from reta.settings import browser_environment, provider_credentials


@dataclass(frozen=True, slots=True)
class BrowserOptions:
    state_dir: Path = Path(".reta/browser")
    headed: bool = False
    allow_private_network: bool = False
    cdp_url: str | None = None
    consent_shared_browser: bool = False


def _profile(config: ProviderConfig, options: BrowserOptions) -> Path:
    profile = options.state_dir / config.id
    for component in [profile, *profile.parents]:
        if component.is_symlink():
            raise RetaError(
                "unsafe_profile", "Linked browser profile rejected"
            )
    marker = profile / ".reta-owned"
    if profile.exists() and not marker.is_file():
        raise RetaError(
            "unsafe_profile", "Refusing an unowned browser profile"
        )
    profile.mkdir(parents=True, exist_ok=True)
    profile.chmod(0o700)
    marker.write_text(config.id)
    marker.chmod(0o600)
    return profile


def _guard(page: Page, policy: NetworkPolicy) -> None:
    def route_request(route: Route) -> None:
        try:
            policy.check(route.request.url)
        except RetaError:
            route.abort("blockedbyclient")
            return
        # Do not let the HTTP client's automatic redirects bypass the guard.
        try:
            response = route.fetch(max_redirects=0)
            route.fulfill(response=response)
        except PlaywrightError:
            route.abort("failed")

    page.route("**/*", route_request)
    page.route_web_socket("**/*", lambda socket: socket.close())
    page.on("popup", lambda popup: popup.close())


@contextmanager
def open_page(
    config: ProviderConfig,
    options: BrowserOptions,
) -> Iterator[Page]:
    policy = NetworkPolicy(
        config,
        allow_private_network=options.allow_private_network,
    )
    policy.check(config.data_url)
    with sync_playwright() as playwright:
        owned_context: BrowserContext | None = None
        state_path: Path | None = None
        if options.cdp_url:
            validate_cdp_endpoint(
                options.cdp_url,
                consent=options.consent_shared_browser,
            )
            browser = playwright.chromium.connect_over_cdp(options.cdp_url)
            if not browser.contexts:
                raise RetaError(
                    "missing_context", "Attached browser has no profile"
                )
            context = browser.contexts[0]
        else:
            profile = _profile(config, options)
            state_path = profile / "auth-state.json"
            if state_path.is_symlink():
                raise RetaError("unsafe_profile", "Linked auth state rejected")
            context = playwright.chromium.launch_persistent_context(
                str(profile),
                headless=not options.headed,
                service_workers="block",
                env=browser_environment(),
            )
            owned_context = context
            if state_path.is_file():
                state = json.loads(state_path.read_text())
                context.add_cookies(state["cookies"])
        page = context.new_page()
        page.set_default_timeout(config.timeout_ms)
        _guard(page, policy)
        try:
            yield page
        finally:
            if not page.is_closed():
                page.close()
            if owned_context is not None:
                write_json(state_path, owned_context.storage_state())
                owned_context.close()
            # Playwright disconnects on exit; never close an attached browser.


def _authenticated(page: Page, config: ProviderConfig) -> bool:
    if not config.require_authentication:
        return True
    return page.locator(config.authenticated_selector).is_visible()


def login(config: ProviderConfig, options: BrowserOptions) -> dict[str, Any]:
    if options.cdp_url:
        raise RetaError(
            "isolated_login_only",
            "No credential injection into shared browsers",
        )
    with open_page(config, options) as page:
        page.goto(config.data_url, wait_until="domcontentloaded")
        if _authenticated(page, config):
            return {
                "provider": config.id,
                "status": "authenticated",
                "reused": True,
            }
        _fill_login(page, config, options)
        try:
            page.locator(config.authenticated_selector).wait_for(
                state="visible"
            )
        except PlaywrightTimeoutError:
            raise RetaError(
                "needs_user_action",
                "Login not verified; handle credentials/MFA/consent",
            ) from None
        return {
            "provider": config.id,
            "status": "authenticated",
            "reused": False,
        }


def _fill_login(
    page: Page,
    config: ProviderConfig,
    options: BrowserOptions,
) -> None:
    required = [
        config.login_url,
        config.username_selector,
        config.password_selector,
        config.submit_selector,
    ]
    if not all(required):
        raise RetaError(
            "needs_user_action", "Reviewed login selectors are required"
        )
    policy = NetworkPolicy(
        config,
        allow_private_network=options.allow_private_network,
    )
    policy.check(config.login_url)
    page.goto(config.login_url, wait_until="domcontentloaded")
    if origin(page.url) != origin(config.login_url):
        raise RetaError(
            "login_origin_changed", "Refusing to fill a redirected login"
        )
    credentials = provider_credentials(config.id)
    page.locator(config.username_selector).fill(
        credentials.username.get_secret_value()
    )
    page.locator(config.password_selector).fill(
        credentials.password.get_secret_value()
    )
    page.locator(config.submit_selector).click()


TABLE_SCRIPT = """(table, maxRows) => {
    const first = table.rows[0];
    if (!first || !first.querySelector('th')) {
        throw new Error('A table header is required');
    }
    const columns = Array.from(first.cells, cell => cell.innerText.trim());
    const rows = [];
    for (let i = 1; i < table.rows.length && rows.length < maxRows; i++) {
        const cells = Array.from(table.rows[i].cells);
        if (cells.some(cell => cell.rowSpan !== 1 || cell.colSpan !== 1)) {
            throw new Error('Merged table cells require an explicit adapter');
        }
        if (cells.length !== columns.length) {
            throw new Error('Table column mismatch');
        }
        rows.push(Object.fromEntries(cells.map((cell, index) =>
            [columns[index], cell.innerText.trim()])));
    }
    return {columns, rows, truncated: table.rows.length - 1 > rows.length};
}"""


def _capture(page: Page, config: ProviderConfig, remaining: int) -> dict:
    table = page.locator(config.table_selector)
    table.wait_for(state="visible")
    if table.count() != 1:
        raise RetaError("ambiguous_table", "Select exactly one data table")
    captured = table.evaluate(TABLE_SCRIPT, remaining)
    columns = captured["columns"]
    if len(set(columns)) != len(columns) or not all(columns):
        raise RetaError(
            "ambiguous_columns", "Unique nonempty headers are required"
        )
    return captured


def _next_page(page: Page, config: ProviderConfig) -> bool:
    if not config.next_selector:
        return False
    control = page.locator(config.next_selector)
    if control.count() == 0:
        return False
    if not control.is_enabled():
        return False
    before = page.locator(config.table_selector).inner_text()
    control.click()
    page.wait_for_function(
        "args => document.querySelector(args.selector)?.innerText "
        "!== args.before",
        arg={"selector": config.table_selector, "before": before},
    )
    return True


def collect(
    config: ProviderConfig,
    options: BrowserOptions,
    output_root: Path,
) -> dict[str, Any]:
    if not config.table_selector:
        raise RetaError("missing_table_selector", "Configure table_selector")
    with open_page(config, options) as page:
        page.goto(config.data_url, wait_until="domcontentloaded")
        if not _authenticated(page, config):
            raise RetaError(
                "needs_user_action", "Log in before collecting evidence"
            )
        return _collect_pages(page, config, output_root)


def _collect_pages(
    page: Page,
    config: ProviderConfig,
    output_root: Path,
) -> dict[str, Any]:
    rows, pages, seen = [], [], set()
    stop_reason = "page_limit"
    for _ in range(config.max_pages):
        captured = _capture(page, config, config.max_rows - len(rows))
        serialized = json.dumps(captured, sort_keys=True).encode()
        fingerprint = hashlib.sha256(serialized).hexdigest()
        if fingerprint in seen:
            stop_reason = "repeated_page"
            break
        seen.add(fingerprint)
        captured_page = {
            **captured,
            "page_url": public_url(page.url),
            "captured_at": datetime.now(UTC).isoformat(),
        }
        proposed = json.dumps([*pages, captured_page]).encode()
        if len(proposed) > config.max_bytes:
            stop_reason = "byte_limit"
            break
        pages.append(captured_page)
        rows.extend(captured["rows"])
        if captured["truncated"] or len(rows) >= config.max_rows:
            stop_reason = "row_limit"
            break
        try:
            if not _next_page(page, config):
                stop_reason = "loaded_view_exhausted"
                break
        except PlaywrightTimeoutError:
            stop_reason = "pagination_did_not_change"
            break
    return _publish_capture(config, output_root, rows, pages, stop_reason)


def _publish_capture(
    config: ProviderConfig,
    root: Path,
    rows: list,
    pages: list,
    reason: str,
) -> dict[str, Any]:
    with bundle_directory(root, f"collected-{uuid.uuid4().hex[:12]}") as (
        directory,
        destination,
    ):
        coverage = {
            "scope": "loaded_dom",
            "dataset_complete": "unknown",
            "stop_reason": reason,
            "pages": len(pages),
            "rows": len(rows),
        }
        write_json(
            directory / "table.json", {"rows": rows, "coverage": coverage}
        )
        write_json(directory / "pages.json", pages)
        metadata = config.model_dump()
        metadata["data_url"] = public_url(config.data_url)
        if config.login_url:
            metadata["login_url"] = public_url(config.login_url)
        write_json(directory / "provider.json", metadata)
        publish_manifest(
            directory,
            {
                "schema_version": "1",
                "kind": "browser_evidence",
                "source_type": config.source_type,
                "account_role": config.account_role,
                "permission": config.permission,
                "coverage": coverage,
                "untrusted": True,
            },
        )
    return {"bundle": str(destination), "coverage": coverage}
