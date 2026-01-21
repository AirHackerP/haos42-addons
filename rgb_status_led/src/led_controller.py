"""
WS281X LED Controller for RGB Status Indicator

Controls addressable RGB LEDs connected to GPIO18 (PWM0) on Raspberry Pi.
Supports both PWM method (GPIO18/12/13) and SPI method (GPIO10).
"""

import logging
from typing import Tuple

try:
    from rpi_ws281x import PixelStrip, Color, ws
    HAS_WS281X = True
except ImportError:
    HAS_WS281X = False
    logging.warning("rpi_ws281x not available - running in simulation mode")

_LOGGER = logging.getLogger(__name__)

# LED strip configuration for SPI method
LED_FREQ_HZ = 800000      # LED signal frequency in hertz
LED_DMA = 10              # DMA channel to use for generating signal
LED_INVERT = False        # True to invert the signal
LED_CHANNEL = 0           # SPI channel (0 for GPIO10 MOSI)

# Status colors (RGB format - converted to GRB internally)
class StatusColor:
    """Predefined status colors."""
    GREEN = (0, 255, 0)       # All systems OK
    AMBER = (255, 165, 0)     # Updates available
    RED = (255, 0, 0)         # Zigbee/system issues
    BLUE = (0, 0, 255)        # Starting up
    OFF = (0, 0, 0)           # LEDs off
    WHITE = (255, 255, 255)   # Test/bright


class LEDController:
    """Controls WS281X LED strip for status indication."""

    def __init__(
        self,
        gpio_pin: int = 18,
        led_count: int = 8,
        brightness: int = 50,
        use_spi: bool = False
    ):
        """
        Initialize LED controller.

        Args:
            gpio_pin: GPIO pin number (default 18 for PWM0)
            led_count: Number of LEDs in strip
            brightness: LED brightness (0-100)
            use_spi: Use SPI method (requires GPIO10) or PWM method (GPIO18)
        """
        self.gpio_pin = gpio_pin
        self.led_count = led_count
        self.brightness = min(255, max(0, int(brightness * 2.55)))  # Convert 0-100 to 0-255
        self.use_spi = use_spi
        self.strip = None
        self._current_color = StatusColor.OFF
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize the LED strip.

        Returns:
            True if initialization successful, False otherwise
        """
        if not HAS_WS281X:
            _LOGGER.warning("WS281X library not available, running in simulation mode")
            self._initialized = True
            return True

        try:
            if self.use_spi:
                # SPI method - more reliable on Pi 4, uses GPIO10 (SPI0 MOSI)
                # strip_type determines color order (GRB for most WS2812B)
                _LOGGER.info(f"Initializing LED strip using SPI method on GPIO{self.gpio_pin}")
                self.strip = PixelStrip(
                    self.led_count,
                    self.gpio_pin,
                    LED_FREQ_HZ,
                    LED_DMA,
                    LED_INVERT,
                    self.brightness,
                    LED_CHANNEL,
                    strip_type=ws.WS2811_STRIP_GRB
                )
            else:
                # PWM method - uses GPIO18/12/13
                _LOGGER.info(f"Initializing LED strip using PWM method on GPIO{self.gpio_pin}")
                self.strip = PixelStrip(
                    self.led_count,
                    self.gpio_pin,
                    LED_FREQ_HZ,
                    LED_DMA,
                    LED_INVERT,
                    self.brightness,
                    LED_CHANNEL,
                    strip_type=ws.WS2811_STRIP_GRB
                )

            self.strip.begin()
            self._initialized = True
            _LOGGER.info(
                f"LED strip initialized: {self.led_count} LEDs on GPIO{self.gpio_pin} "
                f"({'SPI' if self.use_spi else 'PWM'} method)"
            )
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to initialize LED strip: {e}")
            return False

    def set_color(self, color: Tuple[int, int, int], show: bool = True) -> None:
        """
        Set all LEDs to a specific color.

        Args:
            color: RGB tuple (red, green, blue) each 0-255
            show: Whether to immediately display the color
        """
        if not self._initialized:
            _LOGGER.warning("LED strip not initialized")
            return

        self._current_color = color
        r, g, b = color

        if not HAS_WS281X or self.strip is None:
            _LOGGER.debug(f"[SIM] Setting color to RGB({r}, {g}, {b})")
            return

        try:
            # Set all pixels to the same color
            ws_color = Color(r, g, b)
            for i in range(self.led_count):
                self.strip.setPixelColor(i, ws_color)

            if show:
                self.strip.show()

            _LOGGER.debug(f"Set LED color to RGB({r}, {g}, {b})")
        except Exception as e:
            _LOGGER.error(f"Failed to set LED color: {e}")

    def set_status(self, status: str) -> None:
        """
        Set LEDs to predefined status color.

        Args:
            status: Status name ('ok', 'updates', 'error', 'starting', 'off')
        """
        color_map = {
            'ok': StatusColor.GREEN,
            'green': StatusColor.GREEN,
            'updates': StatusColor.AMBER,
            'amber': StatusColor.AMBER,
            'warning': StatusColor.AMBER,
            'error': StatusColor.RED,
            'red': StatusColor.RED,
            'zigbee': StatusColor.RED,
            'starting': StatusColor.BLUE,
            'blue': StatusColor.BLUE,
            'off': StatusColor.OFF,
            'test': StatusColor.WHITE,
        }

        color = color_map.get(status.lower(), StatusColor.OFF)
        self.set_color(color)
        _LOGGER.info(f"Status set to: {status}")

    def set_brightness(self, brightness: int) -> None:
        """
        Set LED brightness.

        Args:
            brightness: Brightness level 0-100
        """
        self.brightness = min(255, max(0, int(brightness * 2.55)))

        if HAS_WS281X and self.strip is not None:
            self.strip.setBrightness(self.brightness)
            self.strip.show()

        _LOGGER.debug(f"Brightness set to {brightness}%")

    def pulse(self, color: Tuple[int, int, int], duration: float = 1.0) -> None:
        """
        Pulse LEDs with a color (fade in and out).

        Args:
            color: RGB tuple for pulse color
            duration: Total duration of pulse in seconds
        """
        import time

        if not self._initialized or not HAS_WS281X or self.strip is None:
            return

        original_brightness = self.brightness
        steps = 20
        step_delay = duration / (steps * 2)

        try:
            # Fade in
            for i in range(steps):
                self.strip.setBrightness(int((i / steps) * original_brightness))
                self.set_color(color, show=True)
                time.sleep(step_delay)

            # Fade out
            for i in range(steps, 0, -1):
                self.strip.setBrightness(int((i / steps) * original_brightness))
                self.set_color(color, show=True)
                time.sleep(step_delay)

            # Restore original brightness
            self.strip.setBrightness(original_brightness)
        except Exception as e:
            _LOGGER.error(f"Pulse animation failed: {e}")

    def cleanup(self) -> None:
        """Turn off LEDs and cleanup resources."""
        if self._initialized:
            self.set_color(StatusColor.OFF)
            _LOGGER.info("LED controller cleaned up")

    @property
    def current_color(self) -> Tuple[int, int, int]:
        """Get current LED color."""
        return self._current_color

    @property
    def is_initialized(self) -> bool:
        """Check if LED strip is initialized."""
        return self._initialized
