"""Constants for the Netwave camera integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "netwave"

CONF_CAMERA_INFO: Final = "camera_info"
CONF_TIMEOUT: Final = "timeout"

DEFAULT_NAME: Final = "Netwave Camera"
DEFAULT_PORT: Final = 80
DEFAULT_TIMEOUT: Final = 10
DEFAULT_USERNAME: Final = "admin"

SERVICE_SEND_COMMAND: Final = "send_command"

ATTR_COMMAND: Final = "command"
ATTR_PARAMETER: Final = "parameter"

COMMANDS: Final[dict[str, str]] = {
    "move_up": "move_up",
    "move_down": "move_down",
    "move_left": "move_left",
    "move_right": "move_right",
    "move_up_left": "move_up_left",
    "move_up_right": "move_up_right",
    "move_down_left": "move_down_left",
    "move_down_right": "move_down_right",
    "stop_movement": "stop_movement",
    "move_center": "move_center",
    "set_preset": "set_preset",
    "recall_preset": "recall_preset",
    "patrol_horizontal": "patrol_horizontal",
    "stop_patrol_horizontal": "stop_patrol_horizontal",
    "patrol_vertical": "patrol_vertical",
    "stop_patrol_vertical": "stop_patrol_vertical",
    "pelco_patrol_horizontal": "pelco_patrol_horizontal",
    "pelco_stop_patrol_horizontal": "pelco_stop_patrol_horizontal",
    "turn_io_on": "turn_io_on",
    "turn_io_off": "turn_io_off",
    "restart_camera": "restart_camera",
    "factory_reset_camera": "factory_reset_camera",
}

PRESET_COMMANDS: Final[frozenset[str]] = frozenset(
    {"set_preset", "recall_preset"}
)
