"""Platform, diagnostics and service tests — require the HA dev environment."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ballinora_match_tracker.const import (
    CONF_TOKEN,
    CONF_URL,
    DOMAIN,
)
from custom_components.ballinora_match_tracker.coordinator import BallinoraCoordinator
from custom_components.ballinora_match_tracker.model import Fixture

VALID_DATA = {
    CONF_URL: "https://tracker.test",
    CONF_TOKEN: "test-token",
}


def _fixtures() -> dict[str, Fixture]:
    return {
        "f1": Fixture(
            fixture_id="f1",
            home_team="Ballinora",
            away_team="Rivals",
            phase="second_half",
            is_live=True,
            home_goals=2,
            home_points=12,
            home_total=18,
            away_goals=1,
            away_points=9,
            away_total=12,
        )
    }


async def _make_entry(hass) -> tuple[MockConfigEntry, BallinoraCoordinator]:
    entry = MockConfigEntry(domain=DOMAIN, data=VALID_DATA, unique_id=DOMAIN)
    coord = BallinoraCoordinator(hass, entry.data[CONF_URL], entry.data[CONF_TOKEN])
    coord.data = _fixtures()
    entry.runtime_data = coord
    entry.add_to_hass(hass)
    return entry, coord


async def test_platform_entities_added_for_every_fixture(hass):
    entry, _ = _make_entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_ids = hass.states.async_entity_ids()
    fixture_entity_ids = [e for e in entity_ids if e.startswith("sensor.f1_")]
    assert any(e.endswith("_phase") for e in fixture_entity_ids)
    assert any(e.endswith("_combined_score") for e in fixture_entity_ids)
    assert any(e.endswith("_confidence") for e in fixture_entity_ids)

    binary_ids = [e for e in entity_ids if "f1_" in e and "binary_sensor." in e]
    assert any(e.endswith("live") for e in binary_ids)
    assert any(e.endswith("conflict") for e in binary_ids)

    state = hass.states.get("sensor.f1_phase")
    assert state.state == "second_half"
    assert state.attributes["is_live"] is True


async def test_newly_discovered_fixture_adds_entities(hass):
    entry, coord = _make_entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert not hass.states.async_entity_ids("sensor.f2_phase")
    coord.data["f2"] = Fixture(fixture_id="f2", home_team="New", away_team="Team")
    coord.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.f2_phase")
    assert state is not None
    assert state.state == "scheduled"


async def test_entities_unavailable_when_fixture_retained_only(hass):
    # Entities must go unavailable (never be deleted) when a fixture leaves the
    # active payload but is still retained server-side.
    entry, coord = _make_entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coord.last_update_success = True
    coord.data = {}
    coord.async_set_updated_data({})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.f1_phase")
    assert state is not None  # still registered
    assert state.state == "unavailable"


async def test_diagnostics_never_contains_token(hass):
    entry, _ = _make_entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    from homeassistant.components.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    payload = await async_get_config_entry_diagnostics(hass, entry)
    assert CONF_TOKEN not in payload["config_entry"]["data"]
    assert VALID_DATA[CONF_TOKEN] not in str(payload)
    assert "test-token" not in str(payload)
    assert payload["runtime"]["fixture_count"] == 1


async def test_refresh_service_available(hass):
    entry, _coord = _make_entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, "refresh")
    # The service must not raise even if the tracker is momentarily down.
    await hass.services.async_call(DOMAIN, "refresh", {}, blocking=True)
