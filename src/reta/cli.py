"""Typed JSON CLI; the same commands work from every shell-capable harness."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from polars.exceptions import PolarsError
from pydantic import ValidationError

from reta import __version__
from reta.artifacts import verify_bundle
from reta.browser.config import ProviderConfig
from reta.browser.details import read_details
from reta.browser.playwright import BrowserOptions, collect, login
from reta.browser.shared import collect_shared
from reta.contracts import (
    AlphaSpec,
    BacktestConfig,
    ImportMapping,
    ResearchRequest,
    RetaError,
)
from reta.data import import_table
from reta.demo import run_demo
from reta.models import backtest_bundle, convert, replay
from reta.research import reverse
from reta.settings import load_environment
from reta.skills import install_skills


def _output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", type=Path, default=Path("output"))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Trading alpha reverse engineering"
    )
    root.add_argument("--version", action="version", version=__version__)
    root.add_argument("--env-file", type=Path, default=Path(".env"))
    commands = root.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Run synthetic numerical recovery")
    _output(demo)
    research = commands.add_parser(
        "reverse", help="Infer and validate an alpha"
    )
    research.add_argument("--request", type=Path, required=True)
    _output(research)
    conversion = commands.add_parser(
        "convert", help="Convert explicit typed rules"
    )
    conversion.add_argument("--spec", type=Path, required=True)
    conversion.add_argument("--bars", type=Path, required=True)
    conversion.add_argument("--backtest-config", type=Path)
    _output(conversion)
    positions = commands.add_parser(
        "positions", help="Replay a verified bundle"
    )
    positions.add_argument("--bundle", type=Path, required=True)
    positions.add_argument("--bars", type=Path, required=True)
    positions.add_argument("--output", type=Path, required=True)
    imported = commands.add_parser(
        "import", help="Map source columns explicitly"
    )
    imported.add_argument("--input", type=Path, required=True)
    imported.add_argument("--mapping", type=Path, required=True)
    imported.add_argument("--output", type=Path, required=True)
    inspect = commands.add_parser("inspect", help="Verify bundle hashes")
    inspect.add_argument("--bundle", type=Path, required=True)
    backtest = commands.add_parser(
        "backtest", help="Backtest an exported alpha"
    )
    backtest.add_argument("--bundle", type=Path, required=True)
    backtest.add_argument("--bars", type=Path)
    backtest.add_argument("--config", type=Path)
    _output(backtest)
    schemas = commands.add_parser(
        "schema", help="Print authoritative JSON Schema"
    )
    schemas.add_argument(
        "--kind",
        choices=["request", "spec", "provider", "backtest"],
        required=True,
    )
    _skill_parser(commands)
    _browser_parser(commands)
    return root


def _skill_parser(commands: Any) -> None:
    skills = commands.add_parser(
        "skills", help="Install portable harness skills"
    )
    actions = skills.add_subparsers(dest="skill_action", required=True)
    installed = actions.add_parser("install")
    installed.add_argument("--harness", default="codex")
    installed.add_argument("--destination", type=Path)


def _browser_parser(commands: Any) -> None:
    browser = commands.add_parser(
        "browser", help="Authorized browser evidence"
    )
    actions = browser.add_subparsers(dest="browser_action", required=True)
    for action in ["login", "collect", "read", "shared"]:
        selected = actions.add_parser(action)
        selected.add_argument("--provider", type=Path, required=True)
        selected.add_argument(
            "--state-dir", type=Path, default=Path(".reta/browser")
        )
        selected.add_argument("--headed", action="store_true")
        selected.add_argument("--allow-private-network", action="store_true")
        _output(selected)
        if action == "shared":
            selected.add_argument("--browser", required=True)
        else:
            selected.add_argument("--cdp-url")
            selected.add_argument(
                "--consent-shared-browser", action="store_true"
            )


def _browser(args: argparse.Namespace) -> dict[str, Any]:
    provider = ProviderConfig.model_validate_json(args.provider.read_text())
    if args.browser_action == "shared":
        return collect_shared(
            provider,
            args.browser,
            args.output,
            allow_private_network=args.allow_private_network,
        )
    options = BrowserOptions(
        state_dir=args.state_dir,
        headed=args.headed,
        allow_private_network=args.allow_private_network,
        cdp_url=args.cdp_url,
        consent_shared_browser=args.consent_shared_browser,
    )
    try:
        if args.browser_action == "login":
            return login(provider, options)
        if args.browser_action == "read":
            return read_details(provider, options, args.output)
        return collect(provider, options, args.output)
    except PlaywrightError:
        raise RetaError(
            "browser_failure",
            "Browser failed; check selectors, login and Chromium installation",
        ) from None


def dispatch(args: argparse.Namespace) -> dict[str, Any]:
    handlers = {
        "demo": lambda: run_demo(args.output),
        "reverse": lambda: reverse(args.request, args.output),
        "convert": lambda: convert(
            args.spec,
            args.bars,
            args.output,
            backtest=BacktestConfig.model_validate_json(
                args.backtest_config.read_text()
            )
            if args.backtest_config
            else None,
        ),
        "backtest": lambda: backtest_bundle(
            args.bundle,
            args.output,
            bars_path=args.bars,
            config_path=args.config,
        ),
        "positions": lambda: replay(args.bundle, args.bars, args.output),
        "inspect": lambda: verify_bundle(args.bundle),
        "skills": lambda: install_skills(args.harness, args.destination),
        "browser": lambda: _browser(args),
        "import": lambda: import_table(
            args.input,
            ImportMapping.model_validate_json(args.mapping.read_text()),
            args.output,
        ),
        "schema": lambda: {
            "request": ResearchRequest,
            "spec": AlphaSpec,
            "provider": ProviderConfig,
            "backtest": BacktestConfig,
        }[args.kind].model_json_schema(),
    }
    return handlers[args.command]()


def main() -> None:
    args = parser().parse_args()
    load_environment(args.env_file)
    try:
        result = dispatch(args)
    except RetaError as error:
        print(
            json.dumps({"error": {"code": error.code, "message": str(error)}})
        )
        code = 3 if error.code == "needs_user_action" else 2
        raise SystemExit(code) from None
    except ValidationError as error:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "invalid_contract",
                        "fields": [
                            str(item["loc"]) for item in error.errors()
                        ],
                    }
                }
            )
        )
        raise SystemExit(2) from None
    except (OSError, ValueError, KeyError, PolarsError):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "invalid_input",
                        "message": "Check input files and required fields",
                    }
                }
            )
        )
        raise SystemExit(2) from None
    print(json.dumps(result, indent=2, allow_nan=False))
    if result.get("outcome") in {
        "insufficient_evidence",
        "no_candidate_passed",
    }:
        sys.exit(4)


if __name__ == "__main__":
    main()
