"""Netwave camera integration for Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CAMERA_INFO,
    CONF_TIMEOUT,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DOMAIN,
    SERVICE_SEND_COMMAND,
)
from .netwave_api import NetwaveCamera
from .services import async_register_services

PLATFORMS: list[Platform] = [Platform.CAMERA]


@dataclass
class NetwaveRuntimeData:
    """Runtime data stored on the config entry."""

    api: NetwaveCamera
    info: dict[str, str]


NetwaveConfigEntry = ConfigEntry[NetwaveRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: NetwaveConfigEntry) -> bool:
    """Set up Netwave camera from a config entry."""
    address = f"http://{entry.data[CONF_HOST]}:{int(entry.data[CONF_PORT])}/"
    api = NetwaveCamera(
        address,
        entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
        entry.data.get(CONF_PASSWORD, ""),
        int(entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
    )
    entry.runtime_data = NetwaveRuntimeData(
        api=api,
        info=entry.data.get(CONF_CAMERA_INFO, {}),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    hass.data.setdefault(DOMAIN, set()).add(entry.entry_id)
    async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: NetwaveConfigEntry) -> bool:
    """Unload a Netwave camera config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entries: set[str] = hass.data.get(DOMAIN, set())
        entries.discard(entry.entry_id)
        if not entries:
            hass.data.pop(DOMAIN, None)
            if hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):
                hass.services.async_remove(DOMAIN, SERVICE_SEND_COMMAND)

    return unload_ok
