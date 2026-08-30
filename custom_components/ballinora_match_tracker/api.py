"""Thin asynchronous client for the Ballinora Match Tracker API.

No network I/O happens anywhere except in this module; entities only ever read
the coordinator's cached data. The access token only ever travels in the
``Authorization`` header and is never logged, exposed in diagnostics or stored
anywhere except the encrypted config entry.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

import aiohttp

from .const import (
    API_ACTIVE_FIXTURES_PATH,
    API_CHECK_SOURCES_PATH,
    HTTP_TIMEOUT_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

HTTP_OK = 200
HTTP_TOO_MANY_REQUESTS = 429


class BallinoraApiError(Exception):
    """Base class for tracker API errors."""


class AuthenticationError(BallinoraApiError):
    """The access token was rejected (HTTP 401/403)."""


class ConnectionFailed(BallinoraApiError):
    """The tracker could not be reached."""


class RateLimitError(BallinoraApiError):
    """The tracker applied a rate limit (HTTP 429)."""

    def __init__(self, message: str = "Rate limited", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


def redact_url(url: str | None) -> str | None:
    """Strip any credentials that might be embedded in a tracker URL."""
    if not url:
        return url
    from urllib.parse import urlsplit, urlunsplit

    parts = urlsplit(url)
    if "@" in parts.netloc:
        # Keep only host:port after stripping user:password@.
        netloc = parts.netloc.rsplit("@", 1)[-1]
        return urlunsplit(parts._replace(netloc=netloc, query="", fragment=""))
    return urlunsplit(parts._replace(query="", fragment=""))


class BallinoraApiClient:
    """Batched client for the Ballinora Match Tracker API."""

    def __init__(self, session: aiohttp.ClientSession, url: str, token: str) -> None:
        self._session = session
        self._base_url = url.rstrip("/") + "/"
        self._token = token

    def _build_url(self, path: str) -> str:
        return urljoin(self._base_url, path)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    async def _request(self, path: str, method: str = "GET") -> dict[str, Any]:
        url = self._build_url(path)
        try:
            async with asyncio.timeout(HTTP_TIMEOUT_SECONDS):
                async with self._session.request(
                    method, url, headers=self._headers()
                ) as resp:
                    if resp.status in (401, 403):
                        raise AuthenticationError(
                            f"Tracker rejected the access token (HTTP {resp.status})"
                        )
                    if resp.status == HTTP_TOO_MANY_REQUESTS:
                        retry_after = resp.headers.get("Retry-After")
                        raise RateLimitError(
                            message=(
                                "Source check rate limited by the tracker; "
                                "try again in a little while."
                            ),
                            retry_after=int(retry_after) if retry_after else None,
                        )
                    if resp.status != HTTP_OK:
                        raise BallinoraApiError(
                            f"Tracker returned HTTP {resp.status} for {path}"
                        )
                    return await resp.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise ConnectionFailed(f"Timed out talking to {redact_url(url)}") from err
        except aiohttp.ClientConnectionError as err:
            raise ConnectionFailed(
                f"Could not reach {redact_url(url)}: {err.__class__.__name__}"
            ) from err

    async def async_get_active_fixtures(self) -> dict[str, Any]:
        """Fetch all active and retained fixtures in one batched request."""
        return await self._request(API_ACTIVE_FIXTURES_PATH)

    async def async_check_sources_now(self, fixture_id: str) -> dict[str, Any]:
        """Request a bounded, server-side source check for one fixture."""
        path = API_CHECK_SOURCES_PATH.format(fixture_id=fixture_id)
        return await self._request(path, method="POST")

    async def async_check_connection(self) -> None:
        """Validate credentials/connectivity; raises on any failure."""
        await self.async_get_active_fixtures()

    @staticmethod
    def began_at() -> str:
        """Rendering helper for diagnostics timestamps."""
        return datetime.now(UTC).isoformat()
