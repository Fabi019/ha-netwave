"""Camera platform for the Netwave integration."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import aiohttp
from aiohttp import web
from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import (
    async_aiohttp_proxy_web,
    async_get_clientsession,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COMMANDS, DOMAIN, PRESET_COMMANDS
from .netwave_api import NetwaveCamera, NetwaveError

if TYPE_CHECKING:
    from . import NetwaveConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NetwaveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Netwave camera entity."""
    async_add_entities([NetwaveCameraEntity(entry)])


class NetwaveCameraEntity(Camera):
    """Representation of a Netwave camera."""

    _attr_brand = "Netwave"
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: NetwaveConfigEntry) -> None:
        """Initialize the camera entity."""
        super().__init__()
        self._api: NetwaveCamera = entry.runtime_data.api
        self._attr_unique_id = entry.unique_id or entry.entry_id
        self._attr_model = entry.runtime_data.info.get("model") or "IP Camera"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=entry.title,
            manufacturer="Netwave",
            model=self._attr_model,
        )

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image from the camera."""
        try:
            return await self.hass.async_add_executor_job(self._api.get_snapshot)
        except NetwaveError as err:
            raise HomeAssistantError(
                f"Unable to fetch a snapshot from {self.entity_id}: {err}"
            ) from err

    async def handle_async_mjpeg_stream(
        self, request: web.Request
    ) -> web.StreamResponse | None:
        """Proxy the camera's native MJPEG stream to Home Assistant.

        Rendering the stream through the camera proxy endpoint makes the
        frontend show MJPEG images instead of trying to transcode the stream
        into HLS, which some of these cameras do not support reliably.
        """
        session = async_get_clientsession(self.hass)
        stream_coro = session.get(
            f"{self._api.address}videostream.cgi",
            auth=aiohttp.BasicAuth(self._api.username, self._api.password),
            raise_for_status=True,
        )
        return await async_aiohttp_proxy_web(self.hass, request, stream_coro)

    async def async_send_command(
        self, command: str, parameter: int | None = None
    ) -> None:
        """Send a PTZ or device command to the camera."""
        method_name = COMMANDS.get(command)
        if method_name is None:
            raise ServiceValidationError(f"Unknown Netwave command: {command}")

        if command in PRESET_COMMANDS:
            if parameter is None:
                raise ServiceValidationError(
                    f"The {command} command requires a parameter (preset 1-15)"
                )
            args: tuple[int, ...] = (parameter,)
        else:
            if parameter is not None:
                raise ServiceValidationError(
                    f"The {command} command does not accept a parameter"
                )
            args = ()

        method = getattr(self._api, method_name, None)
        if method is None:
            raise ServiceValidationError(f"Unsupported Netwave command: {command}")

        try:
            await self.hass.async_add_executor_job(partial(method, *args))
        except (NetwaveError, ValueError) as err:
            raise HomeAssistantError(
                f"Failed to send {command} to {self.entity_id}: {err}"
            ) from err
