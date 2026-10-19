from pathlib import Path

import pytest
from dotenv import dotenv_values

from reta.contracts import RetaError
from reta.settings import browser_environment, provider_credentials


@pytest.fixture
def clean_credentials(monkeypatch):
    for prefix in ["RETA_FIXTURE", "RETA_DEFAULT"]:
        for suffix in [
            "USERNAME",
            "PASSWORD",
            "USERNAME_FILE",
            "PASSWORD_FILE",
        ]:
            monkeypatch.delenv(f"{prefix}_{suffix}", raising=False)
    return monkeypatch


@pytest.mark.parametrize("use_files", [False, True])
def test_default_pair_supports_unlisted_provider(
    clean_credentials, tmp_path, use_files
):
    for suffix, value in [
        ("USERNAME", "default-user"),
        ("PASSWORD", "secret"),
    ]:
        name = f"RETA_DEFAULT_{suffix}"
        if use_files:
            path = tmp_path / suffix
            path.write_text(value + "\n")
            clean_credentials.setenv(f"{name}_FILE", str(path))
        else:
            clean_credentials.setenv(name, value)
    credentials = provider_credentials("fixture")
    assert credentials.username.get_secret_value() == "default-user"
    assert credentials.password.get_secret_value() == "secret"
    assert "secret" not in repr(credentials)
    assert not any(key.startswith("RETA_") for key in browser_environment())


def test_provider_pair_wins_and_partial_pair_never_uses_defaults(
    clean_credentials,
):
    clean_credentials.setenv("RETA_DEFAULT_USERNAME", "default-user")
    clean_credentials.setenv("RETA_DEFAULT_PASSWORD", "default-password")
    clean_credentials.setenv("RETA_FIXTURE_USERNAME", "provider-user")
    with pytest.raises(RetaError, match="Set RETA_FIXTURE_PASSWORD"):
        provider_credentials("fixture")
    clean_credentials.setenv("RETA_FIXTURE_PASSWORD", "provider-password")
    credentials = provider_credentials("fixture")
    assert credentials.username.get_secret_value() == "provider-user"
    assert credentials.password.get_secret_value() == "provider-password"


def test_default_conflict_and_missing_file_do_not_fall_back(
    clean_credentials, tmp_path
):
    clean_credentials.setenv("RETA_DEFAULT_USERNAME", "default-user")
    clean_credentials.setenv("RETA_DEFAULT_PASSWORD", "secret")
    path = tmp_path / "missing"
    clean_credentials.setenv("RETA_DEFAULT_PASSWORD_FILE", str(path))
    with pytest.raises(RetaError, match="Use RETA_DEFAULT_PASSWORD"):
        provider_credentials("fixture")
    clean_credentials.delenv("RETA_DEFAULT_PASSWORD")
    with pytest.raises(
        RetaError, match="Cannot read RETA_DEFAULT_PASSWORD_FILE"
    ):
        provider_credentials("fixture")


def test_env_example_lists_inventory_with_blank_secrets():
    values = dotenv_values(Path(__file__).parents[1] / ".env.example")
    providers = [
        "DEFAULT",
        "CTRADER",
        "MQL5",
        "COLLECTIVE2",
        "MYFXBOOK",
        "FXBLUE",
        "BYBIT",
        "OKX",
        "BINANCE",
        "BITGET",
        "CHOBOT",
        "DARWINEX",
        "TRADINGVIEW",
        "ETORO",
        "TRADETRON",
        "ZULUTRADE",
        "SIGNALSTART",
        "COMPOSER",
    ]
    for provider_id in providers:
        for suffix in [
            "USERNAME",
            "PASSWORD",
            "USERNAME_FILE",
            "PASSWORD_FILE",
        ]:
            assert values[f"RETA_{provider_id}_{suffix}"] == ""
