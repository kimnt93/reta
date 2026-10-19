"""Explicit origins and private-network protection for owned browser tabs."""

import ipaddress
import socket
from urllib.parse import urlsplit

from reta.browser.config import ProviderConfig, origin
from reta.contracts import RetaError


class NetworkPolicy:
    def __init__(
        self,
        provider: ProviderConfig,
        *,
        allow_private_network: bool = False,
    ) -> None:
        self.origins = {origin(value) for value in provider.allowed_origins}
        self.allow_private_network = allow_private_network

    def check(self, url: str) -> None:
        try:
            selected_origin = origin(url)
        except ValueError:
            raise RetaError("blocked_url", "Invalid browser target") from None
        if selected_origin not in self.origins:
            raise RetaError("blocked_origin", "Target origin is not approved")
        parsed = urlsplit(url)
        if parsed.scheme != "https" and not self.allow_private_network:
            raise RetaError(
                "insecure_origin", "HTTPS required outside local smoke"
            )
        try:
            addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
        except OSError:
            raise RetaError(
                "dns_failure", "Provider hostname cannot resolve"
            ) from None
        if not self.allow_private_network:
            for entry in addresses:
                if not ipaddress.ip_address(entry[4][0]).is_global:
                    raise RetaError(
                        "private_network", "Private target rejected"
                    )


def validate_cdp_endpoint(url: str, *, consent: bool) -> None:
    if not consent:
        raise RetaError(
            "consent_required", "Explicit shared-browser consent required"
        )
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise RetaError("invalid_cdp", "Use an HTTP loopback CDP endpoint")
    try:
        origin(url)
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 80)
    except (OSError, ValueError):
        raise RetaError("invalid_cdp", "Invalid CDP endpoint") from None
    for entry in addresses:
        if not ipaddress.ip_address(entry[4][0]).is_loopback:
            raise RetaError(
                "invalid_cdp", "CDP endpoint must resolve to loopback"
            )
