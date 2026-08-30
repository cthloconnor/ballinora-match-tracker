"""Config flow for the Ballinora Match Tracker integration.

Single config entry. Supports connection validation, reauthentication (triggered
automatically when the tracker rejects the token) and reconfiguration of both the
tracker URL and the access token.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    AuthenticationError,
    BallinoraApiClient,
    BallinoraApiError,
    ConnectionFailed,
    RateLimitError,
)
from .const import CONF_TOKEN, CONF_URL, DEFAULT_URL, DOMAIN, ENTRY_UNIQUE_ID

_LOGGER = logging.getLogger(__name__)

_LOCALHOSTS = {"localhost", "127.0.0.1", "::1"}

SCHEMA_INITIAL = vol.Schema(
    {
        vol.Required(CONF_URL, default=DEFAULT_URL): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
        ),
        vol.Required(CONF_TOKEN): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)

SCHEMA_REAUTH = vol.Schema(
    {
        vol.Required(CONF_TOKEN): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)


def url_is_safe(url: str | None) -> bool:
    """Validate the URL is absolute HTTPS (HTTP only for loopback hosts)."""
    if not url:
        return False
    try:
        split = urlsplit(url)
    except ValueError:
        return False
    if split.scheme not in {"https", "http"} or not split.netloc:
        return False
    return not (split.scheme == "http" and split.hostname not in _LOCALHOSTS)


class BallinoraMatchTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Ballinora Match Tracker config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial connection step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self._validate_input(user_input)
            if not errors:
                await self.async_set_unique_id(ENTRY_UNIQUE_ID)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Ballinora Match Tracker",
                    data={
                        CONF_URL: user_input[CONF_URL].strip(),
                        CONF_TOKEN: user_input[CONF_TOKEN],
                    },
                )
        return self.async_show_form(
            step_id="user",
            data_schema=SCHEMA_INITIAL,
            errors=errors,
        )

    async def _validate_input(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate URL shape and connection; returns an error map."""
        url = (user_input.get(CONF_URL) or "").strip()
        token = user_input.get(CONF_TOKEN) or ""
        if not url_is_safe(url):
            return {"base": "invalid_url"}
        if not token:
            return {"base": "invalid_auth"}
        client = BallinoraApiClient(async_get_clientsession(self.hass), url, token)
        try:
            await client.async_check_connection()
        except AuthenticationError:
            return {"base": "invalid_auth"}
        except (ConnectionFailed, RateLimitError, TimeoutError):
            return {"base": "cannot_connect"}
        except BallinoraApiError:
            return {"base": "cannot_connect"}
        except Exception:
            _LOGGER.exception("Unexpected error while validating tracker connection")
            return {"base": "unknown"}
        return {}

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Reauthentication flow (token rotation only)."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth and store the replacement token."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            token = user_input[CONF_TOKEN]
            client = BallinoraApiClient(
                async_get_clientsession(self.hass),
                entry.data[CONF_URL],
                token,
            )
            try:
                await client.async_check_connection()
            except AuthenticationError:
                errors = {"base": "invalid_auth"}
            except (ConnectionFailed, RateLimitError, TimeoutError):
                errors = {"base": "cannot_connect"}
            except BallinoraApiError:
                errors = {"base": "cannot_connect"}
            except Exception:
                _LOGGER.exception("Unexpected error during reauthentication")
                errors = {"base": "unknown"}
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, CONF_TOKEN: token},
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=SCHEMA_REAUTH,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow the user to change the tracker URL and/or token."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()
        if user_input is not None:
            errors = await self._validate_input(user_input)
            if not errors:
                await self.async_set_unique_id(ENTRY_UNIQUE_ID)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data={
                        CONF_URL: user_input[CONF_URL].strip(),
                        CONF_TOKEN: user_input[CONF_TOKEN],
                    },
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=(user_input or {}).get(
                            CONF_URL, reconfigure_entry.data[CONF_URL]
                        ),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
                    ),
                    vol.Required(CONF_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    ),
                }
            ),
            errors=errors,
        )
