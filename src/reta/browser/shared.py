"""BrowserSkill sharing through owned sessions; no credential injection."""

import json
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

from reta.artifacts import bundle_directory, publish_manifest, write_json
from reta.browser.config import ProviderConfig, public_url
from reta.browser.policy import NetworkPolicy
from reta.contracts import RetaError
from reta.settings import browser_environment


def _run(arguments: list[str], timeout: float) -> dict[str, Any]:
    executable = shutil.which("bsk")
    if executable is None:
        raise RetaError(
            "missing_browserskill", "Run make install-browser-skill"
        )
    try:
        result = subprocess.run(
            [executable, *arguments, "--json"],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=browser_environment(),
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise RetaError(
            "browser_timeout", "BrowserSkill command timed out"
        ) from None
    if result.returncode:
        raise RetaError(
            "browserskill_unavailable",
            "BrowserSkill failed; check bsk doctor and extension pairing",
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RetaError(
            "browser_protocol", "Expected BrowserSkill JSON"
        ) from None
    if not isinstance(payload, dict):
        raise RetaError(
            "browser_protocol", "Expected a BrowserSkill result object"
        )
    return payload


def collect_shared(
    config: ProviderConfig,
    browser_instance: str,
    output_root: Path,
    *,
    allow_private_network: bool = False,
) -> dict[str, Any]:
    if not config.table_selector:
        raise RetaError(
            "missing_table_selector", "Shared collection requires a table"
        )
    policy = NetworkPolicy(config, allow_private_network=allow_private_network)
    policy.check(config.data_url)
    session = _run(
        [
            "session",
            "start",
            "--browser",
            browser_instance,
        ],
        30,
    )
    session_id = session.get("session_id")
    if not session_id:
        raise RetaError("browser_protocol", "No BrowserSkill session identity")
    try:
        return _collect(config, policy, str(session_id), output_root)
    finally:
        cleanup = _run(["session", "stop", str(session_id)], 30)
        if cleanup.get("failed") or cleanup.get("return_failures"):
            raise RetaError(
                "browser_cleanup_failed", "Session cleanup needs review"
            )
        if session_id not in cleanup.get("stopped", []):
            raise RetaError(
                "browser_cleanup_failed", "Session stop not verified"
            )


def _collect(
    config: ProviderConfig,
    policy: NetworkPolicy,
    session_id: str,
    root: Path,
) -> dict[str, Any]:
    timeout = config.timeout_ms / 1000 + 30
    _run(["navigate", config.data_url, "--session", session_id], timeout)
    with bundle_directory(root, f"collected-{uuid.uuid4().hex[:12]}") as (
        directory,
        destination,
    ):
        target = directory / "table.json"
        _run(
            [
                "extract",
                "table",
                "--session",
                session_id,
                "--selector",
                config.table_selector,
                "--out",
                str(target.resolve()),
                "--max-rows",
                str(min(5000, config.max_rows)),
                "--max-bytes",
                str(min(4_194_304, config.max_bytes)),
                "--timeout-ms",
                str(min(15000, config.timeout_ms)),
            ],
            timeout,
        )
        payload = json.loads(target.read_text())
        source = payload.get("source", {})
        source_url = source.get("page_url") or source.get("url")
        if not source_url:
            raise RetaError(
                "missing_provenance", "Extraction omitted page URL"
            )
        policy.check(source_url)
        for field in ["page_url", "frame_url"]:
            if source.get(field):
                policy.check(source[field])
                source[field] = public_url(source[field])
        write_json(target, payload)
        coverage = payload.get("coverage", {})
        write_json(
            directory / "coverage.json",
            {
                "upstream": coverage,
                "dataset_complete": "unknown",
                "limitation": "Single loaded DOM; pagination is not automatic",
            },
        )
        publish_manifest(
            directory,
            {
                "schema_version": "1",
                "kind": "browserskill_evidence",
                "source_type": config.source_type,
                "permission": config.permission,
                "account_role": config.account_role,
                "untrusted": True,
                "dataset_complete": "unknown",
            },
        )
    return {"bundle": str(destination), "dataset_complete": "unknown"}
