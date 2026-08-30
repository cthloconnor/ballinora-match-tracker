"""Sensor platform: one set of sensors per fixture, plus tracker-level health."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ACTIVE_FIXTURES,
    DOMAIN,
    FIXTURE_DEVICE_PREFIX,
    MANUFACTURER,
    TRACKER_DEVICE_IDENTIFIER,
    TRACKER_LAST_UPDATE,
)
from .coordinator import BallinoraCoordinator
from .model import Fixture, parse_iso_datetime, phase_label

type ValueFn = Callable[[Fixture], Any]
type AttrsFn = Callable[[Fixture], dict[str, Any]]


def _fixture_device_info(fixture_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{FIXTURE_DEVICE_PREFIX}{fixture_id}")},
        manufacturer=MANUFACTURER,
    )


class FixtureSensor(CoordinatorEntity, SensorEntity):
    """Base sensor bound to one fixture device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BallinoraCoordinator,
        fixture_id: str,
        *,
        translation_key: str,
        unique_suffix: str,
        value_fn: ValueFn,
        attrs_fn: AttrsFn | None = None,
        device_class: str | None = None,
        state_class: str | None = None,
        unit: str | None = None,
        icon: str | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        super().__init__(coordinator, context=fixture_id)
        self._fixture_id = fixture_id
        self._value_fn = value_fn
        self._attrs_fn = attrs_fn
        self._attr_device_info = _fixture_device_info(fixture_id)
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{fixture_id}_{unique_suffix}"
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
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

    @property
    def native_value(self) -> Any:
        fix = self.fixture
        if fix is None:
            return None
        return self._value_fn(fix)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fix = self.fixture
        if fix is None or self._attrs_fn is None:
            return None
        return self._attrs_fn(fix)


def _score_attrs(prefix: str) -> AttrsFn:
    def attrs(fix: Fixture) -> dict[str, Any]:
        return {
            f"{prefix}_goals": getattr(fix, f"{prefix}_goals"),
            f"{prefix}_points": getattr(fix, f"{prefix}_points"),
            f"{prefix}_total": getattr(fix, f"{prefix}_total"),
            "score_mismatch": fix.score_mismatch,
        }

    return attrs


def _value_goals_points(prefix: str) -> ValueFn:
    def value(fix: Fixture) -> str:
        return str(getattr(fix, f"{prefix}_score"))

    return value


def _value_total(prefix: str) -> ValueFn:
    def value(fix: Fixture) -> int | None:
        return getattr(fix, f"effective_{prefix}_total")

    return value


def _build_fixture_sensors(
    coordinator: BallinoraCoordinator, fixture_id: str
) -> list[SensorEntity]:
    return [
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="phase",
            unique_suffix="phase",
            value_fn=lambda f: f.phase,
            attrs_fn=lambda f: {
                "label": phase_label(f.phase),
                "is_live": f.is_live,
                "in_play": f.in_play,
                "full_time": f.full_time,
                "lifecycle": f.lifecycle,
                "score_conflict": f.score_mismatch,
            },
            icon="mdi:scoreboard-outline",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="sport",
            unique_suffix="sport",
            value_fn=lambda f: f.sport,
            icon="mdi:whistle",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="home_team",
            unique_suffix="home_team",
            value_fn=lambda f: f.home_team,
            icon="mdi:shield-home-outline",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="away_team",
            unique_suffix="away_team",
            value_fn=lambda f: f.away_team,
            icon="mdi:shield-outline",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="competition",
            unique_suffix="competition",
            value_fn=lambda f: f.competition or "",
            icon="mdi:trophy-outline",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="home_goals_points",
            unique_suffix="home_goals_points",
            value_fn=_value_goals_points("home"),
            attrs_fn=_score_attrs("home"),
            icon="mdi:counter",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="away_goals_points",
            unique_suffix="away_goals_points",
            value_fn=_value_goals_points("away"),
            attrs_fn=_score_attrs("away"),
            icon="mdi:counter",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="home_total",
            unique_suffix="home_total",
            value_fn=_value_total("home"),
            attrs_fn=_score_attrs("home"),
            state_class=SensorStateClass.MEASUREMENT,
            unit="points",
            icon="mdi:numeric-3-circle-outline",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="away_total",
            unique_suffix="away_total",
            value_fn=_value_total("away"),
            attrs_fn=_score_attrs("away"),
            state_class=SensorStateClass.MEASUREMENT,
            unit="points",
            icon="mdi:numeric-3-circle-outline",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="combined_score",
            unique_suffix="combined_score",
            value_fn=lambda f: f.combined_score,
            attrs_fn=lambda f: {
                "home_total": f.effective_home_total,
                "away_total": f.effective_away_total,
                "score_mismatch": f.score_mismatch,
            },
            icon="mdi:soccer-field",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="total_points",
            unique_suffix="total_points",
            value_fn=lambda f: f.effective_home_total + f.effective_away_total,
            state_class=SensorStateClass.MEASUREMENT,
            unit="points",
            icon="mdi:numeric-9-plus-box-outline",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="scheduled_at",
            unique_suffix="scheduled_at",
            device_class=SensorDeviceClass.TIMESTAMP,
            value_fn=lambda f: parse_iso_datetime(f.scheduled_at),
            attrs_fn=lambda f: {"timezone": f.timezone},
            icon="mdi:calendar-clock",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="venue",
            unique_suffix="venue",
            value_fn=lambda f: f.venue or "",
            icon="mdi:stadium-outline",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="confidence",
            unique_suffix="confidence",
            value_fn=lambda f: (
                round(f.confidence * 100, 1) if f.confidence is not None else None
            ),
            attrs_fn=lambda f: {"confidence_raw": f.confidence},
            state_class=SensorStateClass.MEASUREMENT,
            unit=PERCENTAGE,
            icon="mdi:gauge",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="confidence_label",
            unique_suffix="confidence_label",
            value_fn=lambda f: f.confidence_label or "",
            attrs_fn=lambda f: {"selection_reason": f.selection_reason},
            icon="mdi:clipboard-check-outline",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="source_coverage",
            unique_suffix="source_coverage",
            value_fn=lambda f: f.source_coverage or "",
            attrs_fn=lambda f: {"transport_health": f.transport_health},
            icon="mdi:radar",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="selected_source",
            unique_suffix="selected_source",
            value_fn=lambda f: f.source_id or "",
            attrs_fn=lambda f: {"source_url": f.source_url},
            icon="mdi:database",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="source_freshness",
            unique_suffix="source_freshness",
            device_class=SensorDeviceClass.DURATION,
            value_fn=lambda f: f.source_freshness_seconds,
            attrs_fn=lambda f: {
                "source_published_at": f.source_published_at,
                "last_source_check_at": f.last_source_check_at,
            },
            state_class=SensorStateClass.MEASUREMENT,
            unit="s",
            icon="mdi:timer-sand",
        ),
        FixtureSensor(
            coordinator,
            fixture_id,
            translation_key="last_source_check",
            unique_suffix="last_source_check",
            device_class=SensorDeviceClass.TIMESTAMP,
            value_fn=lambda f: parse_iso_datetime(f.last_source_check_at),
            icon="mdi:clock-check-outline",
        ),
    ]


class TrackerSensor(CoordinatorEntity, SensorEntity):
    """Integration-level sensor on the tracker device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BallinoraCoordinator,
        *,
        translation_key: str,
        unique_id: str,
        device_class: str | None = None,
        state_class: str | None = None,
        unit: str | None = None,
        icon: str | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, TRACKER_DEVICE_IDENTIFIER)},
            manufacturer=MANUFACTURER,
        )
        self._attr_translation_key = translation_key
        self._attr_unique_id = unique_id
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_entity_category = entity_category


class ActiveFixturesSensor(TrackerSensor):
    """Number of fixtures currently present in the canonical cache."""

    @property
    def native_value(self) -> int | None:
        return len(self.coordinator.data)


class TrackerLastUpdateSensor(TrackerSensor):
    """Timestamp of the last successful download from the tracker."""

    @property
    def native_value(self) -> Any:
        return parse_iso_datetime(
            self.coordinator.last_refresh_at or self.coordinator.last_update
        )


def _build_tracker_sensors(
    coordinator: BallinoraCoordinator,
) -> list[SensorEntity]:
    return [
        ActiveFixturesSensor(
            coordinator,
            translation_key=ACTIVE_FIXTURES,
            unique_id="tracker_active_fixtures",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:format-list-numbered",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        TrackerLastUpdateSensor(
            coordinator,
            translation_key=TRACKER_LAST_UPDATE,
            unique_id="tracker_last_update",
            device_class=SensorDeviceClass.TIMESTAMP,
            icon="mdi:update",
        ),
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BallinoraCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add every fixture sensor plus the tracker-level health sensors."""
    coordinator = entry.runtime_data
    async_add_entities(_build_tracker_sensors(coordinator))

    def _sync() -> None:
        added: list[SensorEntity] = []
        for fixture_id in list(coordinator.data):
            key = f"sensor:{fixture_id}"
            if key not in coordinator.observed_platform_fixtures:
                coordinator.observed_platform_fixtures.add(key)
                added.extend(_build_fixture_sensors(coordinator, fixture_id))
        if added:
            async_add_entities(added)

    _sync()
    unsub = coordinator.async_add_listener(_sync)
    entry.async_on_unload(unsub)
