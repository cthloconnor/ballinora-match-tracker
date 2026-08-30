"""Ballinora Match Tracker integration.

Canonical source of truth is the Ballinora Match Tracker API
(https://ballinora-match-tracker.cthloconnor.workers.dev). A single batched
request keeps every active and retained fixture fresh through a
:class:`DataUpdateCoordinator`; fixtures become devices and their entities are
added dynamically as matches appear.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

from .const import CONF_TOKEN, CONF_URL, DOMAIN, PLATFORMS, SERVICE_REFRESH
from .coordinator import BallinoraCoordinator
from .registry import (
    async_get_or_create_tracker_device,
    async_reconcile_fixture_devices,
)

_LOGGER = logging.getLogger(__name__)

#: platform -> unique registration key used to track the per-fixture entity set.
ENTITY_PREFIX = "fixture"

type BallinoraConfigEntry = ConfigEntry[BallinoraCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BallinoraConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    coordinator = BallinoraCoordinator(
        hass,
        url=entry.data[CONF_URL],
        token=entry.data[CONF_TOKEN],
    )
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        # Home Assistant will surface the reauthentication flow to the user.
        raise
    except ConfigEntryNotReady as err:
        raise ConfigEntryNotReady("Tracker not reachable yet") from err

    # Nothing about the token belongs in transferable data; it lives in the
    # encrypted config entry and never leaves it.
    entry.runtime_data = coordinator

    await async_get_or_create_tracker_device(hass, entry.entry_id)

    await async_reconcile_fixture_devices(hass, entry.entry_id, coordinator.data)

    async def _reconcile_devices() -> None:
        await async_reconcile_fixture_devices(hass, entry.entry_id, coordinator.data)

    # Any refresh may surface brand-new fixtures -> reconcile the device
    # registry each time (cheap; registry calls are idempotent).
    coordinator.async_add_listener(_reconcile_devices)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _async_refresh_service(call) -> None:
        """Canonical refresh only — never triggers upstream source checks."""
        await coordinator.async_request_refresh()

    entry.async_on_unload(
        hass.services.async_register(DOMAIN, SERVICE_REFRESH, _async_refresh_service)
    )

    entry.async_on_unload(coordinator.async_remove_listener(_reconcile_devices))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: BallinoraConfigEntry) -> bool:
    """Tear down the integration cleanly."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: BallinoraConfigEntry) -> None:
    """Best-effort tidy-up when the user removes the integration.

    Devices are left alone except the singleton tracker device so fixture
    history keeps working if the integration is re-added later.
    """
    try:
        ent_reg = er.async_get(hass)
        for entity in list(ent_reg.entities.values()):
            if entity.config_entry_id == entry.entry_id:
                ent_reg.async_remove(entity.entity_id)
    except Exception:
        _LOGGER.debug("Entity cleanup during removal failed", exc_info=True)
