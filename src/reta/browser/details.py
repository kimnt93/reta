"""Read a reviewed strategy description without forms or browser state."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from reta.artifacts import bundle_directory, publish_manifest, write_json
from reta.browser.config import ProviderConfig, origin, public_url
from reta.browser.playwright import BrowserOptions, _authenticated, open_page
from reta.contracts import RetaError

DETAIL_SCRIPT = """(element, maxBytes) => {
    const excluded = 'script,style,noscript,template,form,input,textarea,' +
        'select,button,[contenteditable],[hidden],[aria-hidden="true"]';
    if (element === document.body || element === document.documentElement ||
        element.closest(excluded)) {
        return {invalid: true};
    }
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const parts = [];
    let bytes = 0;
    let truncated = false;
    while (walker.nextNode()) {
        const parent = walker.currentNode.parentElement;
        if (!parent || parent.closest(excluded)) {
            continue;
        }
        if (!parent.checkVisibility({visibilityProperty: true,
                opacityProperty: true})) {
            continue;
        }
        const text = walker.currentNode.textContent.trim();
        if (!text) continue;
        const size = new TextEncoder().encode(text).length + 1;
        if (bytes + size > maxBytes) {
            truncated = true;
            break;
        }
        parts.push(text);
        bytes += size;
    }
    return {text: parts.join('\\n'), truncated};
}"""

LINK_SCRIPT = """(links, limit) => {
    const visible = links.filter(a => a.checkVisibility({
        visibilityProperty: true, opacityProperty: true
    }) && !a.closest('form,[contenteditable],[hidden],[aria-hidden="true"]'));
    return {
        urls: visible.slice(0, limit).map(a => a.href),
        truncated: visible.length > limit
    };
}"""


def read_details(
    config: ProviderConfig,
    options: BrowserOptions,
    output_root: Path,
) -> dict[str, Any]:
    if not config.detail_selector:
        raise RetaError("missing_detail_selector", "Configure detail_selector")
    with open_page(config, options) as page:
        page.goto(config.data_url, wait_until="domcontentloaded")
        if not _authenticated(page, config):
            raise RetaError(
                "needs_user_action", "Log in before reading strategy details"
            )
        selected = page.locator(config.detail_selector)
        selected.wait_for(state="visible")
        if selected.count() != 1:
            raise RetaError("ambiguous_detail", "Select one strategy detail")
        content = selected.evaluate(DETAIL_SCRIPT, config.max_bytes)
        if content.get("invalid"):
            raise RetaError(
                "unsafe_detail_selector", "Select strategy content, not a page"
            )
        if not content["text"]:
            raise RetaError("empty_detail", "No visible strategy text found")
        links = selected.locator("a[href]").evaluate_all(
            LINK_SCRIPT, config.max_rows
        )
        location = public_url(page.url)
    return _publish_details(config, output_root, content, location, links)


def _publish_details(
    config: ProviderConfig,
    root: Path,
    content: dict,
    location: str,
    links: dict,
) -> dict[str, Any]:
    approved_links = set()
    approved_origins = {origin(value) for value in config.allowed_origins}
    for value in links["urls"]:
        try:
            url = urljoin(location, value)
            if origin(url) in approved_origins:
                approved_links.add(public_url(url))
        except ValueError:
            continue
    payload = {
        **content,
        "provider_id": config.id,
        "detail_selector": config.detail_selector,
        "allowed_origins": sorted(approved_origins),
        "source_url": location,
        "captured_at": datetime.now(UTC).isoformat(),
        "links": sorted(approved_links),
        "links_truncated": links["truncated"],
        "permission": config.permission,
        "source_type": config.source_type,
        "account_role": config.account_role,
        "untrusted": True,
    }
    payload["truncated"] = content["truncated"] or links["truncated"]
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if len(serialized.encode()) > config.max_bytes:
        raise RetaError("detail_byte_limit", "Increase reviewed max_bytes")
    with bundle_directory(root, f"details-{uuid.uuid4().hex[:12]}") as (
        directory,
        destination,
    ):
        write_json(directory / "details.json", payload)
        publish_manifest(
            directory,
            {
                "schema_version": "1",
                "kind": "strategy_details",
                "dataset_complete": "unknown",
                "scope": "selected_loaded_dom",
                "untrusted": True,
                "truncated": payload["truncated"],
            },
        )
    return {"bundle": str(destination), "truncated": payload["truncated"]}
