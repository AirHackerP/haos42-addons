# RGB LED Controller Add-on

WS281X RGB LED controller service for Home Assistant. Control addressable LEDs via HTTP API from your automations and scripts.

Designed for the 52Pi Mini Tower case (ZP-0129) but works with any WS281X LED setup.

## Architecture

This add-on provides **LED control only**. All monitoring logic is handled by Home Assistant automations, giving you complete control over when and why LEDs change color.

The add-on exposes an HTTP API on port 8099 that you can call using `rest_command` from HA.

## Features

- Simple HTTP REST API for LED control
- Support for WS281X/SK6812 addressable RGB LEDs
- Colors: green, amber, red, blue, white, off
- All logic in HA - full flexibility for your use cases

## Hardware Requirements

- Raspberry Pi with WS281X addressable LEDs
- LEDs connected to GPIO18 (PWM0)
- 52Pi ZP-0129 Mini Tower case (or compatible WS281X setup)

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `gpio_pin` | int | 18 | GPIO pin for LED data (PWM0) |
| `led_count` | int | 8 | Number of LEDs in strip |
| `brightness` | int | 50 | LED brightness (1-100%) |

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "RGB LED Controller" add-on
3. Configure GPIO pin and LED count if needed
4. Start the add-on

## Home Assistant Integration

### 1. Add REST Command

Add to your `configuration.yaml`:

```yaml
rest_command:
  set_rgb_led:
    url: "http://192.168.1.99:8099/set_color?color={{ color }}"
    method: GET
```

Replace `192.168.1.99` with your Home Assistant's IP address.

### 2. Create Automations

Example - Set LED based on system status:

```yaml
automation:
  - alias: "RGB LED - All Systems OK"
    trigger:
      - platform: state
        entity_id: binary_sensor.zigbee_connectivity
        to: "on"
    action:
      - service: rest_command.set_rgb_led
        data:
          color: "green"

  - alias: "RGB LED - Zigbee Issues"
    trigger:
      - platform: state
        entity_id: binary_sensor.zigbee_connectivity
        to: "off"
    action:
      - service: rest_command.set_rgb_led
        data:
          color: "red"
```

### 3. Create Helper Sensors

Monitor Zigbee connectivity:

```yaml
template:
  - binary_sensor:
      - name: "Zigbee Connectivity"
        device_class: connectivity
        state: >
          {% set covers = states.cover
            | selectattr('entity_id', 'search', 'lumi')
            | selectattr('state', 'eq', 'unavailable')
            | list %}
          {{ covers | length == 0 }}
```

See `HOMEASSISTANT_EXAMPLE.yaml` for complete configuration examples.

## API Reference

### Endpoints

**GET /set_color?color={color}**

Set LED strip to specified color.

Parameters:
- `color` (required): green, amber, red, blue, white, off

Response:
```json
{
  "status": "ok",
  "color": "green"
}
```

**GET /health**

Health check endpoint.

Response:
```json
{
  "status": "ok",
  "initialized": true
}
```

### Available Colors

| Color | Use Case Example |
|-------|------------------|
| `green` | All systems operational |
| `amber` | Warning / updates available |
| `red` | Error / device offline |
| `blue` | Information / processing |
| `white` | Custom status |
| `off` | Turn off LEDs |

## Example Use Cases

1. **System Status Indicator**
   - Green: All devices online
   - Amber: Updates available
   - Red: Device offline

2. **Security System**
   - Green: Armed/disarmed successfully
   - Red: Alert triggered
   - Blue: Arming countdown

3. **Climate Control**
   - Green: Temperature in range
   - Amber: Approaching threshold
   - Red: Temperature critical

4. **Presence Detection**
   - Green: Everyone home
   - Amber: Someone away
   - Off: House empty

## Troubleshooting

### LEDs not lighting up

1. Check GPIO18 connection
2. Verify add-on is running (should show green LED on startup)
3. Check add-on logs for initialization errors
4. Test API: `curl http://192.168.1.99:8099/health`

### API not responding

1. Verify port 8099 is accessible
2. Check add-on is running
3. Review add-on logs for errors
4. Confirm firewall/network settings

### Permission errors

The add-on requires privileged access to control GPIOs. This is configured automatically - no manual changes needed.

## Pi 4 Compatibility

For Raspberry Pi 4, you may need to add these to `/boot/config.txt`:

```
core_freq=500
core_freq_min=500
```

This fixes CPU frequency scaling issues with PWM timing.

## References

- [52Pi ZP-0129 Wiki](https://wiki.52pi.com/index.php?title=ZP-0129-4wire)
- [rpi_ws281x Library](https://github.com/jgarff/rpi_ws281x)
- [Home Assistant REST Command](https://www.home-assistant.io/integrations/rest_command/)
