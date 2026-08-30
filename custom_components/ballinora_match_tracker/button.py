"""Button platform: per-fixture source re-check and a canonical refresh."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CHECK_SOURCES_NOW,
    DOMAIN,
    FIXTURE_DEVICE_PREFIX,
    LAST_CHECK_RESULT_ATTR,
    MANUFACTURER,
    REFRESH,
    RETRY_AFTER_ATTR,
    TRACKER_DEVICE_IDENTIFIER,
)
from .coordinator import BallinoraCoordinator

_LOGGER = logging.getLogger(__name__)


class FixtureButton(CoordinatorEntity, ButtonEntity):
    """Per-fixture button linked to the fixture device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BallinoraCoordinator,
        fixture_id: str,
        *,
        translation_key: str,
        unique_suffix: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator, context=fixture_id)
        self._fixture_id = fixture_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{FIXTURE_DEVICE_PREFIX}{fixture_id}")},
            manufacturer=MANUFACTURER,
        )
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{fixture_id}_{unique_suffix}"
        self._attr_icon = icon


class CheckSourcesNowButton(FixtureButton):
    """Ask the tracker to re-check every score source for one fixture."""

    def __init__(self, coordinator: BallinoraCoordinator, fixture_id: str) -> None:
        super().__init__(
            coordinator,
            fixture_id,
            translation_key=CHECK_SOURCES_NOW,
            unique_suffix="check_sources_now",
            icon="mdi:cloud-refresh",
        )

    async def async_press(self) -> None:
        """Trigger the bounded source check and surface the result."""
        fixture_id = self._fixture_id
        _LOGGER.debug("Manual source check requested for fixture %s", fixture_id)
        try:
            result = await self.coordinator.async_check_sources(fixture_id)
        except Exception:
            _LOGGER.exception("check-sources failed for fixture %s", fixture_id)
            self._attr_extra_state_attributes = {
                LAST_CHECK_RESULT_ATTR: "failed_unexpectedly",
            }
            self.async_write_ha_state()
            return
        self._attr_extra_state_attributes = {
            LAST_CHECK_RESULT_ATTR: result.message,
            RETRY_AFTER_ATTR: result.retry_after,
        }
        self.async_write_ha_state()


class RefreshButton(CoordinatorEntity, ButtonEntity):
    """Force a canonical re-download of the batched fixture payload."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BallinoraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, TRACKER_DEVICE_IDENTIFIER)},
            manufacturer=MANUFACTURER,
        )
        self._attr_translation_key = REFRESH
        self._attr_unique_id = "tracker_refresh"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Canonical refresh only – never triggers upstream source checks."""
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BallinoraCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the tracker refresh button plus one check-sources button per fixture."""
    coordinator = entry.runtime_data
    async_add_entities([RefreshButton(coordinator)])

    def _sync() -> None:
        added: list[ButtonEntity] = []
        for fixture_id in list(coordinator.data):
            key = f"button:{fixture_id}"
            if key not in coordinator.observed_platform_fixtures:
                coordinator.observed_platform_fixtures.add(key)
                added.append(CheckSourcesNowButton(coordinator, fixture_id))
        if added:
            async_add_entities(added)

    _sync()
    unsub = coordinator.async_add_listener(_sync)
    entry.async_on_unload(unsub)
