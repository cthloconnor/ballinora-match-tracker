"""Coordinator tests — require the Home Assistant dev environment."""

from __future__ import annotations

from custom_components.ballinora_match_tracker.coordinator import (
    BallinoraCoordinator,
    clamp_refresh_interval,
)


def test_clamp_refresh_interval_bounds():
    assert clamp_refresh_interval(None) == 60
    assert clamp_refresh_interval(None, has_live=True) == 30
    assert clamp_refresh_interval(10) == 30
    assert clamp_refresh_interval(5000) == 900
    assert clamp_refresh_interval(120) == 120
    assert clamp_refresh_interval("garbage") == 60


async def test_coordinator_refresh_populates_data(hass, monkeypatch):
    async def _fake(self):
        return {
            "generated_at": "2026-08-30T12:00:00+01:00",
            "timezone": "Europe/Dublin",
            "recommended_refresh_seconds": 90,
            "fixtures": [
                {
                    "id": "f1",
                    "home_team": "A",
                    "away_team": "B",
                    "phase": "second_half",
                    "is_live": True,
                    "home_goals": 1,
                    "home_points": 5,
                    "home_total": 8,
                },
                {
                    "id": "f2",
                    "home_team": "C",
                    "away_team": "D",
                },
            ],
        }

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_get_active_fixtures",
        _fake,
    )
    coord = BallinoraCoordinator(hass, "https://tracker.test", "tok")
    await coord.async_refresh()

    assert set(coord.data) == {"f1", "f2"}
    assert coord.data["f1"].in_play is True
    assert coord.data["f1"].score_mismatch is False
    assert coord.data["f2"].phase == "scheduled"
    assert coord.last_refresh_at == "2026-08-30T12:00:00+01:00"
    assert coord.update_interval.total_seconds() == 90


async def test_coordinator_auth_failure_raises_config_entry_auth_failed(
    hass, monkeypatch
):
    from homeassistant.exceptions import ConfigEntryAuthFailed

    from custom_components.ballinora_match_tracker.api import AuthenticationError

    async def _bad(self):
        raise AuthenticationError("token rejected")

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_get_active_fixtures",
        _bad,
    )
    coord = BallinoraCoordinator(hass, "https://tracker.test", "tok")
    try:
        await coord.async_refresh()
    except ConfigEntryAuthFailed:
        return
    raise AssertionError("expected ConfigEntryAuthFailed")


async def test_check_sources_result_messages(hass, monkeypatch):
    coord = BallinoraCoordinator(hass, "https://tracker.test", "tok")

    async def _ok(self):
        return {"ok": True}

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_check_sources_now",
        _ok,
    )
    assert (await coord.async_check_sources("f1")).message == "completed"

    from custom_components.ballinora_match_tracker.api import RateLimitError

    async def _limited(self):
        raise RateLimitError(retry_after=45)

    monkeypatch.setattr(
        "custom_components.ballinora_match_tracker.api.BallinoraApiClient"
        ".async_check_sources_now",
        _limited,
    )
    result = await coord.async_check_sources("f1")
    assert result.message == "rate_limited"
    assert result.retry_after == 45
