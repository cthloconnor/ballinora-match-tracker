"""Binary sensor platform: live/conflict/operator-attention flags per fixture."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BROKEN_ICON,
    CONFLICT_ICON,
    DOMAIN,
    FIXTURE_DEVICE_PREFIX,
    LIVE_ICON,
    MANUFACTURER,
    TRACKER_DEVICE_IDENTIFIER,
)
from .coordinator import BallinoraCoordinator
from .model import Fixture


def _fixture_device_info(fixture_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{FIXTURE_DEVICE_PREFIX}{fixture_id}")},
        manufacturer=MANUFACTURER,
    )


class FixtureBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base binary sensor bound to one fixture device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BallinoraCoordinator,
        fixture_id: str,
        *,
        translation_key: str,
        unique_suffix: str,
        device_class: str | None = None,
        icon: str | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        super().__init__(coordinator, context=fixture_id)
        self._fixture_id = fixture_id
        self._attr_device_info = _fixture_device_info(fixture_id)
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{fixture_id}_{unique_suffix}"
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_entity_category = entity_category

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and self._fixture_id in self.coordinator.data
        )

    @property
    def fixture(self) -> Fixture | None:
        return self.coordinator.data.get(self._fixture_id)


class LiveBinarySensor(FixtureBinarySensor):
    """True while the match is live (any in-progress phase)."""

    def __init__(self, coordinator: BallinoraCoordinator, fixture_id: str) -> None:
        super().__init__(
            coordinator,
            fixture_id,
            translation_key="live",
            unique_suffix="live",
        )

    @property
    def is_on(self) -> bool | None:
        fix = self.fixture
        return fix.is_live if fix is not None else None

    @property
    def icon(self) -> str:
        return LIVE_ICON if self.is_on else "mdi:bell-sleep-outline"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {"phase": self.fixture.phase if self.fixture else ""}


class ConflictBinarySensor(FixtureBinarySensor):
    """True when score sources disagree and the tracker cannot reconcile."""

    def __init__(self, coordinator: BallinoraCoordinator, fixture_id: str) -> None:
        super().__init__(
            coordinator,
            fixture_id,
            translation_key="conflict",
            unique_suffix="conflict",
            device_class=BinarySensorDeviceClass.PROBLEM,
            icon=CONFLICT_ICON,
        )

    @property
    def is_on(self) -> bool | None:
        fix = self.fixture
        return fix.score_mismatch if fix is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fix = self.fixture
        if fix is None or not fix.score_mismatch:
            return None
        return {
            "detail": f"goals*3 {fix.home_goals}+{fix.away_goals} "
            f"!= totals {fix.home_total}+{fix.away_total}",
        }


class OperatorAttentionBinarySensor(FixtureBinarySensor):
    """True when the tracker operator asks for human attention."""

    def __init__(self, coordinator: BallinoraCoordinator, fixture_id: str) -> None:
        super().__init__(
            coordinator,
            fixture_id,
            translation_key="operator_attention",
            unique_suffix="operator_attention",
            device_class=BinarySensorDeviceClass.PROBLEM,
            icon=BROKEN_ICON,
        )

    @property
    def is_on(self) -> bool | None:
        fix = self.fixture
        return fix.operator_attention if fix is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, str | None] | None:
        fix = self.fixture
        if fix is None:
            return None
        return {
            "message": fix.operator_attention_message,
            "phase": fix.phase,
        }


class TrackerOpsAttentionBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Integration-level: true when any retained fixture needs attention."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BallinoraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, TRACKER_DEVICE_IDENTIFIER)},
            manufacturer=MANUFACTURER,
        )
        self._attr_translation_key = "tracker_ops_attention"
        self._attr_unique_id = "tracker_ops_attention"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_icon = BROKEN_ICON
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        return any(fix.operator_attention for fix in self.coordinator.data.values())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BallinoraCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add binary sensors (tracker-level once, fixture-level on discovery)."""
    coordinator = entry.runtime_data
    async_add_entities([TrackerOpsAttentionBinarySensor(coordinator)])

    def _sync() -> None:
        added: list[BinarySensorEntity] = []
        for fixture_id in list(coordinator.data):
            key = f"binary_sensor:{fixture_id}"
            if key not in coordinator.observed_platform_fixtures:
                coordinator.observed_platform_fixtures.add(key)
                added.append(LiveBinarySensor(coordinator, fixture_id))
                added.append(ConflictBinarySensor(coordinator, fixture_id))
                added.append(OperatorAttentionBinarySensor(coordinator, fixture_id))
        if added:
            async_add_entities(added)

    _sync()
    unsub = coordinator.async_add_listener(_sync)
    entry.async_on_unload(unsub)
