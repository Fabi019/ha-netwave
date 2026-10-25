"""Small synchronous client for Netwave-compatible IP cameras.

This module is based on TheLogicMaster/Netwave-Camera (WTFPL):
https://github.com/TheLogicMaster/Netwave-Camera
"""

from __future__ import annotations

import re
from urllib.parse import quote, urlparse

import requests
from requests.auth import HTTPBasicAuth


class NetwaveError(Exception):
    """Base exception for Netwave camera errors."""


class NetwaveAuthError(NetwaveError):
    """Raised when the camera rejects the credentials."""


class NetwaveConnectionError(NetwaveError):
    """Raised when the camera cannot be reached."""


class NetwaveCamera:
    """A local representation of a Netwave camera."""

    video_mode_50_hz = 0
    video_mode_60_hz = 1
    video_mode_outdoor = 2
    resolution_160_x_120 = 2
    resolution_320_x_240 = 8
    resolution_640_x_480 = 32

    def __init__(
        self,
        address: str,
        username: str = "admin",
        password: str = "",
        timeout: int = 10,
    ) -> None:
        """Initialize the camera client."""
        self.address = address.rstrip("/") + "/"
        self.username = username
        self.password = password
        self._auth = HTTPBasicAuth(username, password)
        self.timeout = timeout

        self._brightness = 0
        self._contrast = 0
        self._resolution = 0
        self._mode = 0
        self._orientation = 0
        self._info: dict[str, str] = {}

    def __str__(self) -> str:
        """Return a debug-friendly representation without the password."""
        return (
            f"NetwaveCamera(address={self.address!r}, "
            f"username={self.username!r}, timeout={self.timeout})"
        )


    def get_brightness(self) -> int:
        """Get the local brightness from 0 to 15."""
        return self._brightness // 16

    def get_contrast(self) -> int:
        """Get the local contrast from 0 to 6."""
        return self._contrast

    def get_resolution(self) -> int:
        """Get the local resolution (2, 8 or 32)."""
        return self._resolution

    def get_mode(self) -> int:
        """Get the local video mode (0 to 2)."""
        return self._mode

    def get_mirror_horizontal(self) -> bool:
        """Get whether the image is horizontally mirrored."""
        return bool(self._orientation & 2)

    def get_mirror_vertical(self) -> bool:
        """Get whether the image is vertically mirrored."""
        return bool(self._orientation & 1)

    def get_orientation(self) -> int:
        """Get the two-bit orientation value."""
        return self._orientation

    def set_brightness(self, brightness: int) -> None:
        """Set the camera's brightness to an integer from 0 to 15."""
        if brightness < 0 or brightness > 15:
            raise ValueError("Brightness must be from 0 to 15")
        self._send_video_value(1, brightness * 16)
        self._brightness = brightness * 16

    def set_contrast(self, contrast: int) -> None:
        """Set the camera's contrast value to an integer from 0 to 6."""
        if contrast < 0 or contrast > 6:
            raise ValueError("Contrast must be from 0 to 6")
        self._send_video_value(2, contrast)
        self._contrast = contrast

    def set_resolution(self, resolution: int) -> None:
        """Set the camera's resolution to 2, 8 or 32."""
        if resolution not in (2, 8, 32):
            raise ValueError("Resolution must be 2, 8 or 32")
        self._send_video_value(0, resolution)
        self._resolution = resolution

    def set_mode(self, mode: int) -> None:
        """Set the camera's video mode to an integer from 0 to 2."""
        if mode < 0 or mode > 2:
            raise ValueError("Mode must be from 0 to 2")
        self._send_video_value(3, mode)
        self._mode = mode

    def set_mirror_horizontal(self, mirrored: bool) -> None:
        """Set the horizontal video mirror state."""
        self.set_orientation(int(self._orientation & 1) + int(mirrored) * 2)

    def set_mirror_vertical(self, mirrored: bool) -> None:
        """Set the vertical video mirror state."""
        self.set_orientation(int(mirrored) + int(self._orientation & 2))

    def set_orientation(self, orientation: int) -> None:
        """Set the two-bit orientation value on the camera."""
        if orientation < 0 or orientation > 3:
            raise ValueError("Orientation must be from 0 to 3")
        self._send_video_value(5, orientation)
        self._orientation = orientation


    def stop_movement(self) -> None:
        """The termination command for the movements."""
        self._send_command(1)

    def move_up(self) -> None:
        """Rotate upward."""
        self._send_command(0)

    def move_down(self) -> None:
        """Rotate downward."""
        self._send_command(2)

    def move_left(self) -> None:
        """Rotate left."""
        self._send_command(4)

    def move_right(self) -> None:
        """Rotate right."""
        self._send_command(6)

    def move_up_left(self) -> None:
        """Rotate up-left."""
        self._send_command(90)

    def move_up_right(self) -> None:
        """Rotate up-right."""
        self._send_command(91)

    def move_down_left(self) -> None:
        """Rotate down-left."""
        self._send_command(92)

    def move_down_right(self) -> None:
        """Rotate down-right."""
        self._send_command(93)

    def move_center(self) -> None:
        """Re-center the camera."""
        self._send_command(25)

    def patrol_vertical(self) -> None:
        """Initiate vertical patrolling."""
        self._send_command(26)

    def stop_patrol_vertical(self) -> None:
        """Terminate vertical patrolling."""
        self._send_command(27)

    def patrol_horizontal(self) -> None:
        """Initiate horizontal patrolling."""
        self._send_command(28)

    def stop_patrol_horizontal(self) -> None:
        """Terminate horizontal patrolling."""
        self._send_command(29)

    def pelco_patrol_horizontal(self) -> None:
        """Initiate Pelco horizontal patrolling."""
        self._send_command(20)

    def pelco_stop_patrol_horizontal(self) -> None:
        """Terminate Pelco horizontal patrolling."""
        self._send_command(21)

    def turn_io_on(self) -> None:
        """Turn on X10 type IO."""
        self._send_command(94)

    def turn_io_off(self) -> None:
        """Turn off X10 type IO."""
        self._send_command(95)

    def set_preset(self, preset: int) -> None:
        """Save the current position to a preset slot from 1 to 15."""
        if preset < 1 or preset > 15:
            raise ValueError("Preset must be from 1 to 15")
        self._send_command(28 + 2 * preset)

    def recall_preset(self, preset: int) -> None:
        """Move to a saved preset slot from 1 to 15."""
        if preset < 1 or preset > 15:
            raise ValueError("Preset must be from 1 to 15")
        self._send_command(29 + 2 * preset)


    def get_alias(self) -> str:
        """Return the camera's alias."""
        return self._info["alias"]

    def get_id(self) -> str:
        """Return the camera's id."""
        return self._info["id"]

    def get_info(self) -> dict[str, str]:
        """Return a dictionary of most camera settings."""
        return self._info

    def restart_camera(self) -> None:
        """Restart the camera."""
        self._send_request("reboot.cgi")

    def factory_reset_camera(self) -> None:
        """Factory reset the camera."""
        self._send_request("restore_factory.cgi")

    def factor_reset_camera(self) -> None:
        """Deprecated alias for :meth:`factory_reset_camera`."""
        self.factory_reset_camera()

    def get_snapshot(self) -> bytes:
        """Get a JPEG snapshot from the camera."""
        return self._send_request("snapshot.cgi").content

    def get_stream_url(self, path: str = "videostream.cgi") -> str:
        """Return an authenticated MJPEG stream URL for the camera.

        The credentials are embedded in the URL because Home Assistant's
        stream component needs them when it opens the stream with FFmpeg.
        """
        parsed = urlparse(self.address)
        host = parsed.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"

        userinfo = (
            f"{quote(self.username, safe='')}:{quote(self.password, safe='')}"
        )
        netloc = f"{userinfo}@{host}"
        if parsed.port:
            netloc += f":{parsed.port}"

        return f"{parsed.scheme}://{netloc}/{path.lstrip('/')}"

    def update_full(self) -> None:
        """Update info and video settings from the camera."""
        self.update_info()
        self.update_video_settings()

    def update_video_settings(self) -> None:
        """Update local video settings from the camera."""
        settings = self._send_fetch("get_camera_params.cgi")
        self._brightness = int(settings["brightness"])
        self._resolution = int(settings["resolution"])
        self._contrast = int(settings["contrast"])
        self._mode = int(settings["mode"])
        self._orientation = int(settings["flip"])

    def update_info(self) -> None:
        """Update local camera info from the camera."""
        self._info = self._send_fetch("get_params.cgi")


    def _send_video_value(self, param: int, value: int) -> None:
        """Send a video parameter to the camera."""
        self._send_request("camera_control.cgi", {"param": param, "value": value})

    def _send_command(self, command: int) -> None:
        """Send a movement command to the camera."""
        self._send_request("decoder_control.cgi", {"command": command})

    def _send_fetch(
        self, path: str, params: dict[str, int] | None = None
    ) -> dict[str, str]:
        """Fetch a dictionary of values from a CGI endpoint."""
        data: dict[str, str] = {}
        for match in re.findall(
            r"(?<= )(.*)(=)('?)(.*[^'])('?)(?=;)",
            self._send_request(path, params).text,
        ):
            data[match[0]] = match[3]
        return data

    def _send_request(
        self, path: str, params: dict[str, int] | None = None
    ) -> requests.Response:
        """Send a GET request to the camera and validate the response."""
        try:
            response = requests.get(
                url=self.address + path,
                params={} if params is None else params,
                auth=self._auth,
                timeout=self.timeout,
            )
        except requests.RequestException as err:
            raise NetwaveConnectionError(str(err)) from err

        if response.status_code == 401:
            raise NetwaveAuthError("Authentication failed")
        if response.status_code != 200:
            raise NetwaveError(
                f"Request failed with HTTP {response.status_code}: "
                f"{response.request.url}"
            )

        return response
