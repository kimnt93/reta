"""The only application environment/secret readers."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from pydantic import SecretStr

from reta.contracts import RetaError


@dataclass(frozen=True, slots=True)
class Credentials:
    username: SecretStr
    password: SecretStr


def load_environment(path: Path) -> None:
    if path.is_file():
        load_dotenv(path, override=False)


def _secret(name: str) -> SecretStr:
    direct = os.environ.get(name)
    filename = os.environ.get(f"{name}_FILE")
    if direct and filename:
        raise RetaError("ambiguous_secret", f"Use {name} or {name}_FILE")
    if filename:
        try:
            direct = Path(filename).read_text().rstrip("\r\n")
        except OSError:
            raise RetaError(
                "unreadable_secret", f"Cannot read {name}_FILE"
            ) from None
    if not direct:
        raise RetaError("missing_secret", f"Set {name} or {name}_FILE")
    return SecretStr(direct)


def provider_credentials(provider_id: str) -> Credentials:
    prefix = f"RETA_{provider_id.upper()}"
    names = [
        f"{prefix}_USERNAME",
        f"{prefix}_USERNAME_FILE",
        f"{prefix}_PASSWORD",
        f"{prefix}_PASSWORD_FILE",
    ]
    # Select a whole pair; incomplete provider credentials must fail.
    if not any(os.environ.get(name) for name in names):
        prefix = "RETA_DEFAULT"
    return Credentials(
        username=_secret(f"{prefix}_USERNAME"),
        password=_secret(f"{prefix}_PASSWORD"),
    )


def browser_environment() -> dict[str, str]:
    allowed = {
        "PATH",
        "HOME",
        "USER",
        "TMPDIR",
        "TEMP",
        "TMP",
        "LANG",
        "LC_ALL",
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XDG_RUNTIME_DIR",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "SYSTEMROOT",
        "PLAYWRIGHT_BROWSERS_PATH",
    }
    return {
        key: value
        for key, value in os.environ.items()
        if key in allowed or key.startswith("BSK_")
    }
