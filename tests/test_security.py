import pytest
from pydantic import ValidationError

from reta.browser.config import ProviderConfig
from reta.browser.policy import NetworkPolicy, validate_cdp_endpoint
from reta.contracts import RetaError
from reta.settings import browser_environment, provider_credentials
from reta.skills import install_skills


def provider(**changes):
    return ProviderConfig.model_validate(
        {
            "id": "fixture",
            "allowed_origins": ["https://127.0.0.1"],
            "data_url": "https://127.0.0.1/data",
            "table_selector": "#history",
            "permission": "Owned fixture",
            "source_type": "paper",
            "account_role": "provider",
            "require_authentication": False,
            **changes,
        }
    )


def test_origin_credentials_and_private_targets_are_rejected():
    with pytest.raises(ValidationError):
        provider(data_url="https://user:secret@127.0.0.1/data")
    with pytest.raises(RetaError, match="Private target"):
        NetworkPolicy(provider()).check("https://127.0.0.1/data")
    with pytest.raises(RetaError, match="origin is not approved"):
        NetworkPolicy(provider()).check("https://example.com/data")


def test_cdp_requires_consent_and_loopback():
    with pytest.raises(RetaError, match="consent"):
        validate_cdp_endpoint("http://127.0.0.1:9222", consent=False)
    with pytest.raises(RetaError, match="loopback"):
        validate_cdp_endpoint("http://192.0.2.1:9222", consent=True)


def test_selected_secret_files_are_private_and_not_passed_to_children(
    monkeypatch, tmp_path
):
    monkeypatch.delenv("RETA_FIXTURE_USERNAME_FILE", raising=False)
    monkeypatch.delenv("RETA_FIXTURE_PASSWORD", raising=False)
    password = tmp_path / "password"
    password.write_text("private-test-password\n")
    monkeypatch.setenv("RETA_FIXTURE_USERNAME", "private-test-user")
    monkeypatch.setenv("RETA_FIXTURE_PASSWORD_FILE", str(password))
    monkeypatch.setenv("UNRELATED_API_KEY", "unrelated-secret")
    credentials = provider_credentials("fixture")
    assert credentials.password.get_secret_value() == "private-test-password"
    assert "private-test-password" not in repr(credentials)
    assert "private-test-user" not in repr(credentials)
    environment = browser_environment()
    assert "RETA_FIXTURE_USERNAME" not in environment
    assert "UNRELATED_API_KEY" not in environment
    monkeypatch.setenv("RETA_FIXTURE_PASSWORD", "another-private-password")
    with pytest.raises(RetaError, match="Use RETA_FIXTURE_PASSWORD"):
        provider_credentials("fixture")


def test_skill_install_preserves_user_edits(tmp_path):
    destination = tmp_path / "skills"
    install_skills("custom", destination)
    existing = destination / "reta-research/SKILL.md"
    existing.write_text("User's custom research instructions")
    with pytest.raises(RetaError, match="Preserving existing"):
        install_skills("custom", destination)
    assert existing.read_text() == "User's custom research instructions"
