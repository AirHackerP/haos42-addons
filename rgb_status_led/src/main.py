#!/usr/bin/env python3
"""
RGB Status LED - Main Entry Point

Monitors Home Assistant status and controls WS281X LEDs to indicate:
- Green: All systems OK
- Amber: Updates available
- Red: Zigbee device issues
"""

import json
import logging
import signal
import sys
import time
from pathlib import Path

from led_controller import LEDController, StatusColor
from ha_monitor import HAMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
_LOGGER = logging.getLogger("rgb_status_led")

# Global for cleanup
led_controller = None


def load_config() -> dict:
    """Load add-on configuration from options.json."""
    config_path = Path("/data/options.json")

    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    # Default configuration
    _LOGGER.warning("No options.json found, using defaults")
    return {
        "gpio_pin": 18,
        "led_count": 8,
        "use_spi": False,
        "brightness": 50,
        "refresh_interval": 30,
        "check_zigbee": True,
        "check_updates": True,
        "zigbee_entity_patterns": ["lumi", "zha", "cover.*acn002"]
    }


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    _LOGGER.info(f"Received signal {signum}, shutting down...")
    if led_controller:
        led_controller.cleanup()
    sys.exit(0)


def main():
    """Main entry point."""
    global led_controller

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    _LOGGER.info("=" * 50)
    _LOGGER.info("RGB Status LED Add-on Starting")
    _LOGGER.info("=" * 50)

    # Load configuration
    config = load_config()
    _LOGGER.info(f"Configuration loaded:")
    _LOGGER.info(f"  GPIO Pin: {config['gpio_pin']}")
    _LOGGER.info(f"  LED Count: {config['led_count']}")
    _LOGGER.info(f"  Use SPI: {config.get('use_spi', True)}")
    _LOGGER.info(f"  Brightness: {config['brightness']}%")
    _LOGGER.info(f"  Refresh Interval: {config['refresh_interval']}s")
    _LOGGER.info(f"  Check Zigbee: {config['check_zigbee']}")
    _LOGGER.info(f"  Check Updates: {config['check_updates']}")

    # Initialize LED controller
    led_controller = LEDController(
        gpio_pin=config["gpio_pin"],
        led_count=config["led_count"],
        brightness=config["brightness"],
        use_spi=config.get("use_spi", True)
    )

    if not led_controller.initialize():
        _LOGGER.error("Failed to initialize LED controller")
        # Continue anyway - might be running in simulation mode

    # Show startup color
    _LOGGER.info("Setting startup indicator (blue)")
    led_controller.set_status("starting")

    # Initialize HA monitor
    monitor = HAMonitor(
        check_zigbee=config["check_zigbee"],
        check_updates=config["check_updates"],
        zigbee_patterns=config.get("zigbee_entity_patterns", [])
    )

    # Wait for HA to be ready
    _LOGGER.info("Waiting for Home Assistant to be ready...")
    time.sleep(10)

    # Main monitoring loop
    _LOGGER.info("Starting status monitoring loop")
    refresh_interval = config["refresh_interval"]
    last_status = None

    while True:
        try:
            # Get current status
            status = monitor.get_status()
            priority = monitor.get_status_priority()

            # Log status changes
            if priority != last_status:
                _LOGGER.info(f"Status changed: {last_status} -> {priority}")

                if status.zigbee_issues:
                    _LOGGER.warning(
                        f"Zigbee issues detected: {status.unavailable_devices}"
                    )
                if status.updates_available:
                    _LOGGER.info(
                        f"Updates available: {status.pending_updates}"
                    )

                last_status = priority

            # Update LED color
            led_controller.set_status(priority)

            # Log current state periodically
            _LOGGER.debug(
                f"Status: {priority} | "
                f"Zigbee OK: {not status.zigbee_issues} | "
                f"Updates: {len(status.pending_updates)}"
            )

        except Exception as e:
            _LOGGER.error(f"Error in monitoring loop: {e}")
            # Set error color on exception
            led_controller.set_color(StatusColor.RED)

        # Wait for next check
        time.sleep(refresh_interval)


if __name__ == "__main__":
    main()
