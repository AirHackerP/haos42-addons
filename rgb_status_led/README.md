# RGB Status LED Add-on

WS281X LED status indicator for Home Assistant, designed for the 52Pi Mini Tower case (ZP-0129).

## Features

- **Green LED**: All systems OK
- **Amber LED**: Home Assistant updates available
- **Red LED**: Zigbee device issues detected
- **Blue LED**: Starting up

## Hardware Requirements

- Raspberry Pi with WS281X addressable LEDs
- LEDs connected to GPIO18 (PWM0)
- 52Pi ZP-0129 Mini Tower case (or compatible WS281X setup)

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `gpio_pin` | int | 18 | GPIO pin for LED data |
| `led_count` | int | 8 | Number of LEDs in strip |
| `brightness` | int | 50 | LED brightness (1-100%) |
| `refresh_interval` | int | 30 | Status check interval (seconds) |
| `check_zigbee` | bool | true | Monitor Zigbee device health |
| `check_updates` | bool | true | Check for available updates |
| `zigbee_entity_patterns` | list | ["lumi", "zha"] | Entity patterns to monitor |

## Prerequisites

1. Enable SPI in `/boot/config.txt`:
   ```
   dtparam=spi=on
   ```

2. Reboot after enabling SPI

## Status Priority

When multiple conditions exist, the LED shows the highest priority status:

1. **Red** (highest): Zigbee devices unavailable
2. **Amber**: Updates available for Core, OS, Supervisor, or add-ons
3. **Green** (lowest): All systems healthy

## Troubleshooting

### LEDs not lighting up

1. Check GPIO18 connection
2. Verify SPI is enabled: `ls /dev/spi*`
3. Check add-on logs for errors

### Permission errors

The add-on requires privileged access. Ensure:
- `full_access: true` in config
- Device mappings for `/dev/mem` and `/dev/spidev*`

## References

- [52Pi ZP-0129 Wiki](https://wiki.52pi.com/index.php?title=ZP-0129-4wire)
- [rpi_ws281x Library](https://github.com/jgarff/rpi_ws281x)
