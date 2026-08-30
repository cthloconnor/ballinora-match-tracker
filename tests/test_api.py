"""Tests for the API client (runs without HA; uses aiohttp + aioresponses)."""

from __future__ import annotations

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses
from yarl import URL

from custom_components.ballinora_match_tracker.api import (
    AuthenticationError,
    BallinoraApiClient,
    ConnectionFailed,
    RateLimitError,
    redact_url,
)
from custom_components.ballinora_match_tracker.const import (
    API_ACTIVE_FIXTURES_PATH,
    API_CHECK_SOURCES_PATH,
)

BASE = "https://tracker.test/"


@pytest_asyncio.fixture
async def client():
    async with aiohttp.ClientSession() as session:
        yield BallinoraApiClient(session, BASE, "sekrit-token")


def test_redact_url():
    assert redact_url("https://user:pass@host.example/path") == (
        "https://host.example/path"
    )
    assert (
        redact_url("https://host.example/path?token=abc") == "https://host.example/path"
    )
    assert redact_url(None) is None


@pytest.mark.asyncio
async def test_active_fixtures_sends_bearer_header(client):
    captured = {}
    with aioresponses() as mocked:
        mocked.get(
            BASE + API_ACTIVE_FIXTURES_PATH,
            payload={"fixtures": [{"id": "1"}]},
            repeat=True,
        )
        await client.async_get_active_fixtures()
        request = mocked.requests[("GET", URL(BASE + API_ACTIVE_FIXTURES_PATH))][0]
        captured["auth"] = request.kwargs["headers"]["Authorization"]
    assert captured["auth"] == "Bearer sekrit-token"


@pytest.mark.asyncio
async def test_active_fixtures_parses_json(client):
    with aioresponses() as mocked:
        mocked.get(BASE + API_ACTIVE_FIXTURES_PATH, payload={"fixtures": []})
        data = await client.async_get_active_fixtures()
    assert data == {"fixtures": []}


@pytest.mark.asyncio
async def test_401_raises_authentication_error(client):
    with aioresponses() as mocked:
        mocked.get(BASE + API_ACTIVE_FIXTURES_PATH, status=401)
        with pytest.raises(AuthenticationError):
            await client.async_get_active_fixtures()


@pytest.mark.asyncio
async def test_403_raises_authentication_error(client):
    with aioresponses() as mocked:
        mocked.get(BASE + API_ACTIVE_FIXTURES_PATH, status=403)
        with pytest.raises(AuthenticationError):
            await client.async_get_active_fixtures()


@pytest.mark.asyncio
async def test_429_surfaces_retry_after(client):
    with aioresponses() as mocked:
        mocked.get(
            BASE + API_ACTIVE_FIXTURES_PATH,
            status=429,
            headers={"Retry-After": "120"},
        )
        with pytest.raises(RateLimitError) as exc:
            await client.async_get_active_fixtures()
    assert exc.value.retry_after == 120


@pytest.mark.asyncio
async def test_429_without_retry_after(client):
    with aioresponses() as mocked:
        mocked.get(BASE + API_ACTIVE_FIXTURES_PATH, status=429)
        with pytest.raises(RateLimitError) as exc:
            await client.async_get_active_fixtures()
    assert exc.value.retry_after is None


@pytest.mark.asyncio
async def test_connection_error_raised_for_unreachable(client):
    with aioresponses() as mocked:
        mocked.get(
            BASE + API_ACTIVE_FIXTURES_PATH,
            exception=aiohttp.ClientConnectionError(),
        )
        with pytest.raises(ConnectionFailed):
            await client.async_get_active_fixtures()


@pytest.mark.asyncio
async def test_check_sources_now_posts(client):
    with aioresponses() as mocked:
        url = BASE + API_CHECK_SOURCES_PATH.format(fixture_id="fx-1")
        mocked.post(url, payload={"ok": True})
        data = await client.async_check_sources_now("fx-1")
    assert data == {"ok": True}
