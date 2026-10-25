"""Config flow for the Netwave camera integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_CAMERA_INFO,
    CONF_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DOMAIN,
)
from .netwave_api import (
    NetwaveAuthError,
    NetwaveCamera,
    NetwaveConnectionError,
    NetwaveError,
)

_LOGGER = logging.getLogger(__name__)


def _normalize_host(host: str) -> str:
    """Accept a bare host, a URL, or a URL with a trailing slash."""
    host = host.strip()
    for prefix in ("http://", "https://"):
        if host.lower().startswith(prefix):
            host = host[len(prefix) :]
            break
    return host.rstrip("/")


def _validate_input(data: dict[str, Any]) -> dict[str, str]:
    """Connect to the camera and return its info dictionary."""
    api = NetwaveCamera(
        f"http://{data[CONF_HOST]}:{int(data[CONF_PORT])}/",
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        int(data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
    )
    api.update_info()

    snapshot = api.get_snapshot()
    if not snapshot.startswith(b"\xff\xd8"):
        raise NetwaveAuthError(
            "The camera did not return a JPEG snapshot; check the credentials"
        )

    return api.get_info()


def _data_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the setup form schema, keeping values after a validation error."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_HOST, default=defaults.get(CONF_HOST, "")
            ): TextSelector(),
            vol.Required(
                CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1, max=65535, mode=NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_USERNAME,
                default=defaults.get(CONF_USERNAME, DEFAULT_USERNAME),
            ): TextSelector(),
            vol.Optional(
                CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")
            ): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
            vol.Optional(
                CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
            ): TextSelector(),
            vol.Optional(
                CONF_TIMEOUT, default=defaults.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=60,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
        }
    )


class NetwaveConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a Netwave camera."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = dict(user_input)
            data[CONF_HOST] = _normalize_host(data[CONF_HOST])
            # NumberSelector returns floats; ports and timeouts must be ints.
            data[CONF_PORT] = int(data[CONF_PORT])
            if CONF_TIMEOUT in data:
                data[CONF_TIMEOUT] = int(data[CONF_TIMEOUT])

            try:
                info = await self.hass.async_add_executor_job(
                    _validate_input, data
                )
            except NetwaveAuthError:
                errors["base"] = "invalid_auth"
            except NetwaveConnectionError:
                errors["base"] = "cannot_connect"
            except NetwaveError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error while connecting to camera")
                errors["base"] = "unknown"
            else:
                camera_id = info.get("id")
                unique_id = (
                    f"camera_{camera_id}"
                    if camera_id
                    else f"{data[CONF_HOST]}:{data[CONF_PORT]}"
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                name = data.get(CONF_NAME, "").strip()
                if not name:
                    name = info.get("alias") or DEFAULT_NAME

                data[CONF_NAME] = name
                data[CONF_CAMERA_INFO] = info
                return self.async_create_entry(title=name, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_data_schema(user_input),
            errors=errors,
        )
