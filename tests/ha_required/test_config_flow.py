"""Config flow tests — require the Home Assistant dev environment.

Run with ``pytest tests/`` after installing the HA test stack
(``pip install -e .[test]`` equivalent for this repo; see docs/testing.md).
"""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ballinora_match_tracker.api import (
    AuthenticationError,
    ConnectionFailed,
)
from custom_components.ballinora_match_tracker.config_flow import url_is_safe
from custom_components.ballinora_match_tracker.const import CONF_TOKEN, CONF_URL, DOMAIN

VALID_DATA = {
    CONF_URL: "https://ballinora-match-tracker.cthloconnor.workers.dev",
    CONF_TOKEN: "test-token",
}


def test_url_is_safe():
    assert url_is_safe("https://tracker.example")
    assert url_is_safe("http://localhost:8080")
    assert url_is_safe("http://127.0.0.1")
    assert not url_is_safe("http://tracker.example")
    assert not url_is_safe("ftp://tracker.example")
    assert not url_is_safe("")
    assert not url_is_safe(None)


async def test_user_step_success_creates_entry(hass, monkeypatch):
    async def _ok(self):
        return None

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_check_connection",
        _ok,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], VALID_DATA
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_URL] == VALID_DATA[CONF_URL]


async def test_user_step_invalid_auth(hass, monkeypatch):
    async def _bad(self):
        raise AuthenticationError("nope")

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_check_connection",
        _bad,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], VALID_DATA
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_step_cannot_connect(hass, monkeypatch):
    async def _unreachable(self):
        raise ConnectionFailed("down")

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_check_connection",
        _unreachable,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], VALID_DATA
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_step_invalid_url_rejected_before_network(hass, monkeypatch):
    called = False

    async def _ok(self):
        nonlocal called
        called = True

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_check_connection",
        _ok,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://tracker.example", CONF_TOKEN: "x"},
    )
    assert result["errors"] == {"base": "invalid_url"}
    assert called is False


async def test_single_entry_unique_id(hass, monkeypatch):
    async def _ok(self):
        return None

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_check_connection",
        _ok,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], VALID_DATA
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY

    # A second entry must be aborted.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], VALID_DATA
    )
    assert result["type"] == FlowResultType.ABORT


async def test_reauth_flow_updates_token_only(hass, monkeypatch):
    entry = MockConfigEntry(
        domain=DOMAIN, data=dict(VALID_DATA), unique_id="ballinora_match_tracker"
    )
    entry.add_to_hass(hass)

    async def _ok(self):
        return None

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_check_connection",
        _ok,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH},
        data=entry.data,
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TOKEN: "rotated-token"}
    )
    assert result["type"] == FlowResultType.ABORT
    assert entry.data[CONF_TOKEN] == "rotated-token"
    assert entry.data[CONF_URL] == VALID_DATA[CONF_URL]
