# Netwave Camera for Home Assistant

A local Home Assistant custom integration for old Netwave IP
cameras with pan/tilt support. It creates a camera entity and the
`netwave.send_command` action.

## Installation

### Manual

1. Copy the `custom_components/netwave` folder into your Home Assistant
   configuration directory:

   ```text
   /config/custom_components/netwave/
   ```

2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **Netwave Camera** and enter:

   | Field | Example |
   | --- | --- |
   | Host | `192.168.1.123` |
   | Port | `80` |
   | Username | `admin` |
   | Password | your camera password |
   | Name | `My camera` |

### HACS

Add this folder as a custom repository in HACS, then install **Netwave
Camera** and restart Home Assistant.

## The `netwave.send_command` action

The action targets one or more Netwave camera entities. Both, the legacy
`service_data` and the modern `target`/`data` form work.

### Command list

| Command | Description |
| --- | --- |
| `move_up` | Tilt up |
| `move_down` | Tilt down |
| `move_left` | Pan left |
| `move_right` | Pan right |
| `move_up_left` | Move up-left |
| `move_up_right` | Move up-right |
| `move_down_left` | Move down-left |
| `move_down_right` | Move down-right |
| `stop_movement` | Stop the current movement |
| `move_center` | Auto-center the camera |
| `set_preset` | Save the current position to a preset slot (1–15) |
| `recall_preset` | Move to a preset slot (1–15) |
| `patrol_horizontal` | Start horizontal patrol |
| `stop_patrol_horizontal` | Stop horizontal patrol |
| `patrol_vertical` | Start vertical patrol |
| `stop_patrol_vertical` | Stop vertical patrol |
| `pelco_patrol_horizontal` | Start Pelco horizontal patrol |
| `pelco_stop_patrol_horizontal` | Stop Pelco horizontal patrol |
| `turn_io_on` | Turn IO on |
| `turn_io_off` | Turn IO off |
| `restart_camera` | Reboot the camera |
| `factory_reset_camera` | Restore factory defaults |

The `parameter` field is required for `set_preset` and `recall_preset` and
must be between `1` and `15`. It must not be supplied for any other command.

### Modern syntax

```yaml
action: perform-action
perform_action: netwave.send_command
target:
  entity_id: camera.my_camera
data:
  command: move_up
```

### Legacy syntax

```yaml
tap_action:
  action: call-service
  service: netwave.send_command
  service_data:
    command: move_up
    entity_id: camera.my_camera
```

## Lovelace card

A ready-to-use `picture-elements` card can be found in the original repo: <https://github.com/TheLogicMaster/Netwave-Camera/blob/master/docs/lovelace.yaml>

## Credits and license

The camera protocol client is based on
[TheLogicMaster/Netwave-Camera](https://github.com/TheLogicMaster/Netwave-Camera),
released under the WTFPL.
