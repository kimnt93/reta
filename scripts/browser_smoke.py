"""Exercise real login, paginated collection and consented CDP ownership."""

import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class FixtureSite(BaseHTTPRequestHandler):
    username = "fixture-user"
    password = secrets.token_urlsafe(24)
    session = secrets.token_urlsafe(24)

    def log_message(self, *args: object) -> None:
        """Never log request bodies or authentication values."""

    def _html(self, body: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/untouched":
            self._html(
                "<title>User tab</title><h1>Leave this user tab alone</h1>"
            )
            return
        authenticated = f"session={self.session}" in self.headers.get(
            "Cookie", ""
        )
        if parsed.path == "/login" or not authenticated:
            self._html(
                "<form method='post' action='/login'>"
                "<input id='username' name='username'>"
                "<input id='password' name='password' type='password'>"
                "<button type='submit'>Sign in</button></form>",
            )
            return
        page = parse_qs(parsed.query).get("page", ["1"])[0]
        next_control = "<a id='next' href='/data?page=2'>Next</a>"
        if page == "2":
            next_control = "<button id='next' disabled>Next</button>"
        quantity = 2 if page == "1" else -2
        self._html(
            "<title>Authorized fixture data</title>"
            "<h1 id='auth'>Signed in</h1>"
            "<table id='history'><tr>"
            "<th>Symbol</th><th>Time</th><th>NetQty</th></tr>"
            f"<tr><td>X</td><td>2026-01-01T0{page}:00:00Z</td>"
            f"<td>{quantity}</td></tr></table>{next_control}",
        )

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        values = parse_qs(self.rfile.read(size).decode())
        valid = values.get("username") == [self.username]
        valid = valid and values.get("password") == [self.password]
        if not valid:
            self._html("<h1>Invalid login or human action required</h1>", 401)
            return
        self.send_response(303)
        self.send_header("Location", "/data")
        self.send_header(
            "Set-Cookie",
            f"session={self.session}; HttpOnly; SameSite=Lax; Path=/",
        )
        self.end_headers()


def cli(
    arguments: list[str], environment: dict[str, str]
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "reta.cli", *arguments],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=90,
    )


def require_success(result: subprocess.CompletedProcess) -> dict:
    if result.returncode:
        raise AssertionError(f"CLI failed: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def provider(base_url: str) -> dict:
    return {
        "id": "fixture",
        "allowed_origins": [base_url],
        "data_url": f"{base_url}/data",
        "login_url": f"{base_url}/login",
        "username_selector": "#username",
        "password_selector": "#password",
        "submit_selector": "button[type=submit]",
        "authenticated_selector": "#auth",
        "table_selector": "#history",
        "next_selector": "#next",
        "permission": "Owned local test fixture",
        "source_type": "paper",
        "account_role": "provider",
        "timeout_ms": 3000,
    }


def run_smoke(temporary: Path, base_url: str) -> dict:
    config = temporary / "provider.json"
    config.write_text(json.dumps(provider(base_url)))
    environment = dict(os.environ)
    environment["RETA_FIXTURE_USERNAME"] = FixtureSite.username
    environment["RETA_FIXTURE_PASSWORD"] = FixtureSite.password
    output = ROOT / "output" / f"browser-smoke-{secrets.token_hex(4)}"
    common = [
        "--provider",
        str(config),
        "--state-dir",
        str(temporary / "state"),
        "--allow-private-network",
        "--output",
        str(output),
    ]
    authenticated = require_success(
        cli(["browser", "login", *common], environment)
    )
    collected = require_success(
        cli(["browser", "collect", *common], environment)
    )
    assert authenticated["status"] == "authenticated"
    assert collected["coverage"]["rows"] == 2
    assert collected["coverage"]["pages"] == 2
    assert collected["coverage"]["dataset_complete"] == "unknown"
    for path in Path(collected["bundle"]).glob("*.json"):
        content = path.read_text()
        assert FixtureSite.password not in content
        assert FixtureSite.session not in content
    cdp = run_cdp(temporary, base_url, common, environment, output)
    username_file = temporary / "username"
    password_file = temporary / "password"
    username_file.write_text(FixtureSite.username)
    password_file.write_text(FixtureSite.password)
    username_file.chmod(0o600)
    password_file.chmod(0o600)
    file_environment = dict(environment)
    del file_environment["RETA_FIXTURE_USERNAME"]
    del file_environment["RETA_FIXTURE_PASSWORD"]
    file_environment["RETA_FIXTURE_USERNAME_FILE"] = str(username_file)
    file_environment["RETA_FIXTURE_PASSWORD_FILE"] = str(password_file)
    file_login = require_success(
        cli(
            [
                "browser",
                "login",
                *common,
                "--state-dir",
                str(temporary / "file-login"),
            ],
            file_environment,
        )
    )
    assert file_login["status"] == "authenticated"
    environment["RETA_FIXTURE_PASSWORD"] = secrets.token_urlsafe(24)
    bad = cli(
        [
            "browser",
            "login",
            *common,
            "--state-dir",
            str(temporary / "wrong-login"),
        ],
        environment,
    )
    assert bad.returncode == 3, bad.stdout
    assert environment["RETA_FIXTURE_PASSWORD"] not in bad.stdout + bad.stderr
    return {
        "isolated_login": True,
        "secret_file_login": True,
        "paginated_rows": 2,
        "wrong_login_needs_action": True,
        **cdp,
        "evidence": collected["bundle"],
    }


def run_cdp(
    temporary: Path,
    base_url: str,
    common: list[str],
    environment: dict[str, str],
    output: Path,
) -> dict:
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(temporary / "real-browser-fixture"),
            headless=True,
            args=[
                f"--remote-debugging-port={port}",
                "--remote-debugging-address=127.0.0.1",
            ],
        )
        try:
            context.add_cookies(
                [
                    {
                        "name": "session",
                        "value": FixtureSite.session,
                        "url": base_url,
                    }
                ]
            )
            user_tab = context.new_page()
            user_tab.goto(f"{base_url}/untouched")
            previous_count = len(context.pages)
            endpoint = f"http://127.0.0.1:{port}"
            denied = cli(
                ["browser", "collect", *common, "--cdp-url", endpoint],
                environment,
            )
            assert denied.returncode == 2
            result = require_success(
                cli(
                    [
                        "browser",
                        "collect",
                        *common,
                        "--cdp-url",
                        endpoint,
                        "--consent-shared-browser",
                    ],
                    environment,
                )
            )
            assert result["coverage"]["rows"] == 2
            assert len(context.pages) == previous_count
            assert not user_tab.is_closed()
            assert user_tab.title() == "User tab"
            screenshot_tab = context.new_page()
            screenshot_tab.goto(f"{base_url}/data")
            screenshot_tab.screenshot(
                path=str(output / "authenticated-table.png")
            )
            screenshot_tab.close()
        finally:
            context.close()
    return {
        "cdp_collection": True,
        "existing_user_tab_preserved": True,
        "cdp_without_consent_rejected": True,
        "screenshot": str(output / "authenticated-table.png"),
    }


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureSite)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with tempfile.TemporaryDirectory(
            prefix="reta-browser-smoke-"
        ) as directory:
            result = run_smoke(
                Path(directory), f"http://127.0.0.1:{server.server_port}"
            )
        print(json.dumps(result, indent=2))
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == "__main__":
    main()
