"""Device registry management for the Ballinora Match Tracker.

Every fixture becomes one Home Assistant device keyed by a stable identifier
derived from the fixture id. When a fixture leaves the API's retention window
the device (and its entities) are left registered and simply stop receiving
updates; nothing is deleted and history is preserved.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    FIXTURE_DEVICE_PREFIX,
    MANUFACTURER,
    MODEL_TRACKER,
    TRACKER_DEVICE_IDENTIFIER,
)
from .model import Fixture


def _identifiers(fixture_id: str) -> set[tuple[str, str]]:
    return {(DOMAIN, f"{FIXTURE_DEVICE_PREFIX}{fixture_id}")}


async def async_get_or_create_tracker_device(hass: HomeAssistant, entry_id: str) -> str:
    """Create (once) the integration-level tracker device and return its id.

    Health/refresh entities live on this device rather than on any individual
    fixture.
    """
    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=entry_id,
        identifiers={(DOMAIN, TRACKER_DEVICE_IDENTIFIER)},
        name="Ballinora Match Tracker",
        manufacturer=MANUFACTURER,
        model=MODEL_TRACKER,
    )
    return device.id


async def async_reconcile_fixture_devices(
    hass: HomeAssistant,
    entry_id: str,
    fixtures: dict[str, Fixture],
) -> dict[str, str]:
    """Ensure every fixture has a device; returns fixture_id -> device_id.

    Names and model are only refreshed while the user has not customised the
    device, so a renamed device is never clobbered by a later poll.
    """
    dev_reg = dr.async_get(hass)
    mapping: dict[str, str] = {}
    for fixture_id, fixture in fixtures.items():
        identifiers = _identifiers(fixture_id)
        device = dev_reg.async_get_device(identifiers=identifiers)
        if device is None:
            device = dev_reg.async_get_or_create(
                config_entry_id=entry_id,
                identifiers=identifiers,
                name=fixture.device_display_name,
                manufacturer=MANUFACTURER,
                model=fixture.sport,
            )
        elif device.name_by_user is None and (
            device.name != fixture.device_display_name or device.model != fixture.sport
        ):
            dev_reg.async_update_device(
                device.id,
                name=fixture.device_display_name,
                model=fixture.sport,
            )
        mapping[fixture_id] = device.id
    return mapping
