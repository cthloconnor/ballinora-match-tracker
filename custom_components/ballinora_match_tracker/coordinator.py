"""Coordinator that keeps every fixture updated from one batched request."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    AuthenticationError,
    BallinoraApiClient,
    ConnectionFailed,
    RateLimitError,
)
from .const import (
    DEFAULT_LIVE_REFRESH_SECONDS,
    DEFAULT_REFRESH_SECONDS,
    DOMAIN,
    MAX_REFRESH_SECONDS,
    MIN_REFRESH_SECONDS,
)
from .model import Fixture, build_fixture_map

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class CheckSourcesResult:
    """Outcome of a manual ``check-sources-now`` request."""

    message: str
    retry_after: int | None = None


def clamp_refresh_interval(recommended: Any, has_live: bool = False) -> int:
    """Clamp the server-recommended poll interval into sane bounds.

    The tracker is authoritative: we follow ``recommended_refresh_seconds``
    whenever it is present, and only enforce a minimum to stay polite and a
    maximum so single-request polling never becomes a busy loop.
    """
    if recommended is None:
        base = DEFAULT_LIVE_REFRESH_SECONDS if has_live else DEFAULT_REFRESH_SECONDS
    else:
        try:
            base = int(recommended)
        except (TypeError, ValueError):
            base = DEFAULT_REFRESH_SECONDS
    return max(MIN_REFRESH_SECONDS, min(MAX_REFRESH_SECONDS, base))


class BallinoraCoordinator(DataUpdateCoordinator[dict[str, Fixture]]):
    """Fetch the canonical set of fixtures on a server-driven interval.

    One request refreshes every active and retained fixture; there are no
    per-entity pollers. The interval is re-derived from the server's
    ``recommended_refresh_seconds`` after every successful refresh.
    """

    def __init__(self, hass: HomeAssistant, url: str, token: str) -> None:
        self.client = BallinoraApiClient(
            session=async_get_clientsession(hass, verify_ssl=True),
            url=url,
            token=token,
        )
        self.last_refresh_at: str | None = None
        self.last_payload_meta: dict[str, Any] = {}
        self.has_ever_succeeded = False
        #: Fixture keys for which the platform setup has already registered
        #: entities, e.g. ``"sensor:123"``. Guards dynamic entity addition.
        self.observed_platform_fixtures: set[str] = set()
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_REFRESH_SECONDS),
            always_update=True,
        )

    async def _async_update_data(self) -> dict[str, Fixture]:
        try:
            payload = await self.client.async_get_active_fixtures()
        except AuthenticationError as err:
            # Home Assistant turns this into a reauthentication flow for the
            # user without discarding any previously fetched data.
            raise ConfigEntryAuthFailed(str(err)) from err
        except ConnectionFailed as err:
            raise UpdateFailed(str(err)) from err
        except RateLimitError as err:
            raise UpdateFailed(str(err), retry_after=err.retry_after) from err
        except Exception as err:
            _LOGGER.exception("Unexpected error while refreshing fixtures")
            raise UpdateFailed(f"Unexpected tracker error: {err}") from err

        fixtures = build_fixture_map(payload)
        # Server-driven adaptive polling.
        has_live = any(fix.in_play for fix in fixtures.values())
        recommended = payload.get("recommended_refresh_seconds")
        self.update_interval = timedelta(
            seconds=clamp_refresh_interval(recommended, has_live)
        )
        self.last_refresh_at = payload.get("generated_at")
        self.last_payload_meta = {
            "generated_at": payload.get("generated_at"),
            "timezone": payload.get("timezone"),
            "recommended_refresh_seconds": self.update_interval.total_seconds(),
        }
        self.has_ever_succeeded = True
        return fixtures

    async def async_check_sources(self, fixture_id: str) -> CheckSourcesResult:
        """Ask the tracker to re-check every score source for one fixture.

        Returns a result object rather than raising, so the calling button can
        surface a friendly status without taking the integration down.
        """
        try:
            await self.client.async_check_sources_now(fixture_id)
        except AuthenticationError:
            return CheckSourcesResult("authentication_failed")
        except RateLimitError as err:
            return CheckSourcesResult("rate_limited", retry_after=err.retry_after)
        except ConnectionFailed:
            return CheckSourcesResult("connection_failed")
        except Exception:
            _LOGGER.exception("check-sources failed for fixture %s", fixture_id)
            return CheckSourcesResult("failed_unexpectedly")
        return CheckSourcesResult("completed")
