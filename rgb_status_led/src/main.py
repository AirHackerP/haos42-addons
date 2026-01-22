#!/usr/bin/env python3
"""
RGB Status LED Add-on - Service Mode

Exposes HTTP API for direct LED control from Home Assistant.
All monitoring logic handled by HA automations.
"""

import json
import logging
import signal
import sys
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

from led_controller import LEDController, StatusColor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
_LOGGER = logging.getLogger("rgb_led_service")

# Global LED controller
led_controller = None
shutdown_requested = False


def load_config() -> Dict[str, Any]:
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
        "brightness": 50
    }


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    _LOGGER.info(f"Received signal {signum}, shutting down...")
    shutdown_requested = True

    if led_controller:
        led_controller.clear()

    sys.exit(0)


class LEDServiceHandler(BaseHTTPRequestHandler):
    """HTTP request handler for LED control."""

    COLOR_MAP = {
        "green": StatusColor.OK,
        "amber": StatusColor.WARNING,
        "yellow": StatusColor.WARNING,
        "red": StatusColor.ERROR,
        "blue": StatusColor.STARTING,
        "white": StatusColor.WHITE,
        "off": StatusColor.OFF
    }

    def do_GET(self):
        """Handle GET requests."""
        global led_controller

        parsed = urlparse(self.path)

        # Health check endpoint
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "initialized": led_controller is not None and led_controller._initialized
            }).encode())
            return

        # Set color endpoint: /set_color?color=green
        if parsed.path == "/set_color":
            params = parse_qs(parsed.query)
            color_name = params.get('color', [''])[0].lower()

            if not color_name:
                self.send_error(400, "Missing 'color' parameter")
                return

            if color_name not in self.COLOR_MAP:
                self.send_error(400, f"Invalid color. Valid colors: {', '.join(self.COLOR_MAP.keys())}")
                return

            color = self.COLOR_MAP[color_name]
            _LOGGER.info(f"Setting LED color to: {color_name}")

            if led_controller:
                led_controller.set_color(color)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "color": color_name
            }).encode())
            return

        # Unknown endpoint
        self.send_error(404, "Endpoint not found. Available: /health, /set_color?color=green")

    def log_message(self, format, *args):
        """Custom logging to use our logger."""
        _LOGGER.debug(f"{self.address_string()} - {format % args}")


def main():
    """Main entry point."""
    global led_controller

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    _LOGGER.info("=" * 50)
    _LOGGER.info("RGB LED Service Starting")
    _LOGGER.info("=" * 50)

    # Load configuration
    config = load_config()
    _LOGGER.info(f"Configuration:")
    _LOGGER.info(f"  GPIO Pin: {config['gpio_pin']}")
    _LOGGER.info(f"  LED Count: {config['led_count']}")
    _LOGGER.info(f"  Brightness: {config['brightness']}%")

    # Initialize LED controller
    led_controller = LEDController(
        gpio_pin=config["gpio_pin"],
        led_count=config["led_count"],
        brightness=config["brightness"],
        use_spi=False
    )

    if not led_controller.initialize():
        _LOGGER.error("Failed to initialize LED controller")
        # Continue anyway for simulation mode

    # Set startup indicator (blue)
    _LOGGER.info("Setting startup indicator (blue)")
    led_controller.set_color(StatusColor.STARTING)

    # Start HTTP server
    port = 8099
    server = HTTPServer(('0.0.0.0', port), LEDServiceHandler)
    _LOGGER.info(f"HTTP service listening on port {port}")
    _LOGGER.info("Available endpoints:")
    _LOGGER.info("  GET /health - Health check")
    _LOGGER.info("  GET /set_color?color=green - Set LED color")
    _LOGGER.info("  Valid colors: green, amber, red, blue, white, off")

    # Show service is ready (green)
    time.sleep(2)
    led_controller.set_color(StatusColor.OK)
    _LOGGER.info("Service ready - LED set to green")

    # Serve requests
    try:
        while not shutdown_requested:
            server.handle_request()
    except KeyboardInterrupt:
        _LOGGER.info("Interrupted by user")
    except Exception as e:
        _LOGGER.error(f"Unexpected error: {e}")
    finally:
        server.server_close()
        if led_controller:
            led_controller.clear()
        _LOGGER.info("Shutdown complete")


if __name__ == "__main__":
    main()
