"""Diagnostics for the Ballinora Match Tracker integration.

The access token is deliberately never included, and any URL that might embed
credentials is run through :func:`redact_url` before it is returned.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .api import redact_url
from .const import CONF_TOKEN, CONF_URL
from .coordinator import BallinoraCoordinator

TO_REDACT = {CONF_TOKEN: "**REDACTED**"}


def _safe_fixture(fix: Any) -> dict[str, Any]:
    fields = {
        "fixture_id": fix.fixture_id,
        "sport": fix.sport,
        "phase": fix.phase,
        "is_live": fix.is_live,
        "home_team": fix.home_team,
        "away_team": fix.away_team,
        "home_goals_points": str(fix.home_score),
        "away_goals_points": str(fix.away_score),
        "home_total": fix.home_total,
        "away_total": fix.away_total,
        "score_mismatch": fix.score_mismatch,
        "confidence": fix.confidence,
        "confidence_label": fix.confidence_label,
        "conflict": fix.conflict,
        "operator_attention": fix.operator_attention,
        "source_id": fix.source_id,
        "source_url": redact_url(fix.source_url),
        "source_coverage": fix.source_coverage,
        "source_freshness_seconds": fix.source_freshness_seconds,
        "last_source_check_at": fix.last_source_check_at,
        "scheduled_at": fix.scheduled_at,
        "retained_until": fix.retained_until,
        "recommended_refresh_seconds": fix.recommended_refresh_seconds,
    }
    return {k: v for k, v in fields.items() if v is not None}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry[BallinoraCoordinator]
) -> dict[str, Any]:
    """Build a privacy-safe diagnostic payload for the whole integration."""
    coordinator = entry.runtime_data

    devices: list[dict[str, Any]] = []
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    for device in dev_reg.devices.values():
        if device.config_entries is None or entry.entry_id not in device.config_entries:
            continue
        device_entities: list[dict[str, Any]] = []
        for entity in ent_reg.entities.get_entries_for_config_entry_id(entry.entry_id):
            if entity.device_id != device.id:
                continue
            state = hass.states.get(entity.entity_id)
            device_entities.append(
                {
                    "entity_id": entity.entity_id,
                    "entity_category": entity.entity_category,
                    "unique_id": entity.unique_id,
                    "state": state.state if state else None,
                    "attributes": (
                        async_redact_data(dict(state.attributes), TO_REDACT)
                        if state
                        else {}
                    ),
                }
            )
        devices.append(
            {
                "id": device.id,
                "name": device.name,
                "model": device.model,
                "entities": device_entities,
            }
        )

    tracker_fixtures = []
    for fixture_id in sorted(coordinator.data):
        fix = coordinator.data[fixture_id]
        if getattr(fix, "fixture_id", None):
            tracker_fixtures.append(_safe_fixture(fix))

    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "data": {
                CONF_URL: redact_url(entry.data.get(CONF_URL)),
                "token": TO_REDACT[CONF_TOKEN],
            },
        },
        "runtime": {
            "has_ever_succeeded": coordinator.has_ever_succeeded,
            "last_refresh_at": coordinator.last_refresh_at,
            "last_payload_meta": coordinator.last_payload_meta,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "fixture_count": len(coordinator.data),
            "tracker_fixtures": tracker_fixtures,
        },
        "devices": devices,
    }
