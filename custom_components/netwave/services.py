"""Service registration for the Netwave camera integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_component import DATA_INSTANCES

from .const import (
    ATTR_COMMAND,
    ATTR_PARAMETER,
    COMMANDS,
    DOMAIN,
    SERVICE_SEND_COMMAND,
)

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.helpers.service import (  # type: ignore[attr-defined]
        async_register_platform_entity_service,
    )
except ImportError:
    async_register_platform_entity_service = None  # type: ignore[assignment]


SEND_COMMAND_SCHEMA: dict[Any, Any] = {
    vol.Required(ATTR_COMMAND): vol.In(COMMANDS),
    vol.Optional(ATTR_PARAMETER): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=15)
    ),
}


def async_register_services(hass: HomeAssistant) -> None:
    """Register the netwave.send_command service once."""
    if hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):
        return

    if async_register_platform_entity_service is not None:
        async_register_platform_entity_service(
            hass,
            DOMAIN,
            SERVICE_SEND_COMMAND,
            entity_domain="camera",
            func="async_send_command",
            schema=SEND_COMMAND_SCHEMA,
        )
        return

    _async_register_legacy_service(hass)


def _async_register_legacy_service(hass: HomeAssistant) -> None:
    """Register the service on Home Assistant versions without platform services."""
    _LOGGER.debug(
        "Home Assistant does not support platform entity services; "
        "using the Netwave compatibility service handler"
    )

    async def _async_handle_send_command(call: ServiceCall) -> None:
        command: str = call.data[ATTR_COMMAND]
        parameter: int | None = call.data.get(ATTR_PARAMETER)

        component = hass.data.get(DATA_INSTANCES, {}).get("camera")
        if component is None:
            raise ServiceValidationError("The camera integration is not loaded")

        entity_ids = call.data.get(ATTR_ENTITY_ID)
        if entity_ids == ENTITY_MATCH_ALL:
            entities = [
                entity
                for entity in component.entities
                if _is_netwave_entity(entity)
            ]
        else:
            if isinstance(entity_ids, str):
                entity_ids = [
                    entity_id.strip()
                    for entity_id in entity_ids.split(",")
                    if entity_id.strip()
                ]
            if not entity_ids:
                raise ServiceValidationError(
                    "Target at least one Netwave camera entity"
                )

            entities = []
            for entity_id in entity_ids:
                entity = component.get_entity(entity_id)
                if entity is not None and _is_netwave_entity(entity):
                    entities.append(entity)

        if not entities:
            raise ServiceValidationError(
                "No Netwave camera entities matched the target"
            )

        for entity in entities:
            await entity.async_send_command(command, parameter)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_COMMAND,
        _async_handle_send_command,
        schema=cv.make_entity_service_schema(SEND_COMMAND_SCHEMA),
    )


def _is_netwave_entity(entity: Any) -> bool:
    """Return True if the entity belongs to this integration."""
    platform = getattr(entity, "platform", None)
    return (
        platform is not None
        and getattr(platform, "platform_name", None) == DOMAIN
        and hasattr(entity, "async_send_command")
    )
