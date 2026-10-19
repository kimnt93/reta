"""Reviewed provider metadata; credentials never belong in this model."""

from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, model_validator

from reta.contracts import Contract


def origin(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP(S) origins are supported")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are prohibited")
    if not parsed.hostname:
        raise ValueError("URL hostname is missing")
    hostname = parsed.hostname.lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    port = parsed.port
    standard = 443 if parsed.scheme == "https" else 80
    suffix = f":{port}" if port and port != standard else ""
    return f"{parsed.scheme}://{hostname}{suffix}"


def public_url(url: str) -> str:
    """Retain source location without query tokens or fragment state."""
    parsed = urlsplit(url)
    return origin(url) + parsed.path


class ProviderConfig(Contract):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,39}$")
    allowed_origins: list[str] = Field(min_length=1)
    data_url: str
    table_selector: str = Field(min_length=1)
    permission: str = Field(min_length=1)
    source_type: Literal[
        "live", "paper", "backtest", "model_account", "unknown"
    ]
    account_role: Literal["provider", "subscriber", "model_account", "unknown"]
    login_url: str | None = None
    username_selector: str | None = None
    password_selector: str | None = None
    submit_selector: str | None = None
    authenticated_selector: str | None = None
    require_authentication: bool = True
    next_selector: str | None = None
    max_pages: int = Field(default=5, ge=1, le=100)
    max_rows: int = Field(default=5000, ge=1, le=10000)
    max_bytes: int = Field(default=4_000_000, ge=1024, le=20_000_000)
    timeout_ms: int = Field(default=15000, ge=500, le=120000)

    @model_validator(mode="after")
    def validate_origins(self) -> Self:
        approved = set()
        for value in self.allowed_origins:
            normalized = origin(value)
            if value.rstrip("/") != normalized:
                raise ValueError("Allowlist entries must be exact origins")
            approved.add(normalized)
        for value in [self.data_url, self.login_url]:
            if value is not None and origin(value) not in approved:
                raise ValueError("Provider URL outside approved origins")
        if self.require_authentication and not self.authenticated_selector:
            raise ValueError("Authenticated success selector is required")
        return self
